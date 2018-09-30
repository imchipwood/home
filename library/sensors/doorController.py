"""Threaded MQTT Door Control and State Monitoring

Chip Wood, Jan. 2017

This file is a one-stop shop for reading the state of a door as well as
controlling the door, through the use of two GPIO pins and an MQTT connection.

A state monitoring MQTT client thread reads the state sensor at 1Hz.
When the state changes, the new state is published on an MQTT topic.
The published states are "open" and "closed".

A separate control MQTT client thread subscribes to the control topic and
toggles the GPIO when a message is published with the payload of "TOGGLE".
It does not respond to any other messages.
"""
import logging
import json
try:
	import RPi.GPIO as GPIO
except:
	logging.warning("Failed to import RPi.GPIO - using mock library")
	import library.sensors.mock_gpio as GPIO
import paho.mqtt.client as paho
import paho.mqtt.publish as pahopub
import timeit
import pprint
from time import sleep
# from multiprocessing import Process
from threading import Thread

from library.config.doorConfig import DoorConfig
from library.config.pushbulletConfig import PushbulletConfig
from cameraController import PiCameraController
from library.services.pushbulletNotify import PushbulletImageNotify, PushbulletTextNotify

# logging junk
# Level		Numeric value
# CRITICAL	 50
# ERROR		40
# WARNING	  30
# INFO		 20
# DEBUG		10
# NOTSET		0

# { "topic": "home-assistant/garage/switch", "payload": "TOGGLE", "qos": "1", "retain": "false" }


class Error(Exception):
	pass


class MQTTError(Error):
	pass


class DoorController(object):
	"""
	Threaded Door Controller object
	This class is intended to handle all aspects of door monitoring and control, as well as camera control
	Once instantiated, simply call the start() method to launch the threads
	"""
	def __init__(self, doorConfigFile, cameraConfigFile=None, pushbulletConfigFile=None, skipLogging=False, debug=False):
		"""
		Constructor for door controller, handling door monitoring & control, camera control, and notifications
		@param doorConfigFile: path to door sensing/control config file
		@type doorConfigFile: str
		@param cameraConfigFile: path to camera config file
		@type cameraConfigFile: str
		@param pushbulletConfigFile: path to pushbullet config file
		@type pushbulletConfigFile: str
		@param debug: debug flag - enables more verbose logging
		@type debug: bool
		"""
		super(DoorController, self).__init__()
		self.state = None
		self.mqttEnabled = False

		# initalize logger
		self.logger = logging.getLogger(__name__)

		# logging level has to be set globally for some reason
		logging.getLogger().setLevel(logging.DEBUG)

		# read the config files
		self.gpioSettings = {}
		self.settings = DoorConfig(doorConfigFile)
		self.mqttSettings = self.settings.mqtt

		# finish setting up logging
		if not skipLogging:
			self.setupLogging(loggingLevel=debug, logFile=self.settings.log)

		# create the camera
		if cameraConfigFile is not None:
			self.camera = PiCameraController(configFile=cameraConfigFile, debug=debug)
		else:
			self.camera = None

		if pushbulletConfigFile is not None:
			self.pushbulletConfig = PushbulletConfig(pushbulletConfigFile)
			self.pushbullet = self.pushbulletConfig.apiKey
		else:
			self.pushbulletConfig = None
			self.pushbullet = None

		# set up MQTT connections
		self.clientControl = None

		# setup sensing/controlling GPIO
		self.setupGPIO()

		self.monitor = False
		self.monitorThread = Thread(target=self.monitorLoop, args=[])

		self.logCurrentSetup()

	@property
	def open(self):
		"""
		Check if door is open
		@return: whether or not door is open
		@rtype: bool
		"""
		return self.state

	# region Logging

	def setupLogging(self, loggingLevel=False, logFile=None):
		"""
		Set up logging stream and file handlers
		@param loggingLevel: logging level as defined by logging package
		@param logFile: (optional) path for file logging
		"""
		if loggingLevel:
			val = 'DEBUG'
		else:
			val = 'INFO'
		self.logger.info("Logging level: {}".format(val))

		# stdout stream handler
		ch = logging.StreamHandler()
		ch.setLevel(loggingLevel)

		# stdout logging formatting
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)
		ch.setFormatter(stdoutFormatter)

		# remove existing handlers then add the new one
		self.logger.handlers = []
		self.logger.addHandler(ch)

		# set up file handler logger - always debug level
		if logFile:
			fh = logging.FileHandler(logFile)
			fh.setLevel(logging.DEBUG)

			# file logging formatting
			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fh.setFormatter(fileFormatter)
			self.logger.addHandler(fh)
		
	def logCurrentSetup(self):
		"""
		Write the current setup to the debug stream
		"""
		self.logger.debug("\n----------------------------------------")
		self.logger.debug("\nMQTT Settings:\n{}".format(str(self.mqttSettings)))
		self.logger.debug("\nGPIO Settings:\n{}".format(json.dumps(self.gpioSettings, indent=2)))
		self.logger.debug("Camera enabled: {}\n".format(bool(self.camera)))
		self.logger.debug("Notifications enabled: {}\n".format(bool(self.pushbullet)))
		self.logger.debug("----------------------------------------\n")

	# endregion Logging
	# region Threading

	def start(self):
		"""
		Start the state monitoring thread and launch the MQTT connections
		"""
		# begin control loop
		try:
			self.setupMQTT()
		except:
			# if mqtt fails to set up, that's OK, we can at least monitor the door
			logging.exception("door control loop failed to initialize - will not be able to control door")

		sleep(2)

		# launch monitor thread
		try:
			self.logger.debug("starting state thread")
			self.monitor = True
			self.monitorThread.start()
		except:
			self.logger.exception("failed to start state thread")
			self.cleanup()
			raise
		
	def cleanup(self):
		"""
		Clean up all threads and GPIO
		"""
		self.logger.info("cleaning up")

		try:
			self.logger.debug("shutting down monitor loop")
			self.monitor = False
		except Exception as e:
			self.logger.exception("Exception while shutting down monitor loop: {}".format(e))

		if self.mqttEnabled:
			try:
				self.logger.debug("shutting down control thread")
				self.clientControl.loop_stop()
				self.clientControl.unsubscribe(self.mqttSettings['topic_control'])
				self.clientControl.disconnect()
			except Exception as e:
				self.logger.exception("Exception while shutting down control loop: {}".format(e))

		try:
			self.logger.debug("Cleaning up GPIO")
			GPIO.cleanup()
		except Exception as e:
			self.logger.exception("Exception while cleaning up GPIO: {}".format(e))

		if self.camera:
			try:
				self.logger.debug("Cleaning up camera")
				self.camera.cleanup()
			except Exception as e:
				self.logger.exception("Exception while cleaning up camera: {}".format(e))

		# region ThreadLoops

	def monitorLoop(self):
		"""
		Monitor the door open/closed sensor @1Hz
		@note: set DoorController.monitor=False to stop the thread
		"""
		oneHz = 1.0
		lastOneHzTime = 0
		lastDoorState = None

		# Loop until flag is disabled
		while self.monitor:
			now = float(timeit.default_timer())

			if (now - lastOneHzTime) > oneHz:
				# 1Hz loop
				lastOneHzTime = now

				try:
					newState = self.getState()
					if newState != lastDoorState:
						lastDoorState = self.doorStateChange(lastDoorState, newState)

				except:
					self.logger.exception("state exception")
					raise

		self.logger.info("Monitor loop exiting")

	def doorStateChange(self, lastDoorState, newState):
		"""
		Handle changing door state (open->close, vice versa)
		@param lastDoorState: door state last time we checked
		@type lastDoorState: bool
		@param newState: door state now
		@type newState: bool
		@return: current state of door
		@rtype: bool
		"""
		self.state = newState
		self.logger.debug("monitor state: {}".format(self.state))

		# Send out MQTT message
		self.publishDoorState()

		# Did door state change?
		if self.pushbullet and lastDoorState is not None:

			if not self.open:
				# Only send text notification on closing -
				text = "Garage Door {}".format('open' if self.state else 'closed')
				notify = PushbulletTextNotify(self.pushbullet, text, text)
				self.LogPushbulletErrors(notify)
			else:
				logging.info("Door Opened, skipping text notify")

		if self.camera and self.open and lastDoorState is not None:
			# create a separate thread for the camera so this loop can continue running while camera operates
			t = Thread(target=self.cameraLoop, args=[])
			t.start()

		return newState

	@staticmethod
	def LogPushbulletErrors(response):
		if 'error' in response.result:
			for key in ['iden', 'sender_iden', 'receiver_iden']:
				del response.result[key]
			logging.info("PushbulletTextNotify Error:\n{}".format(pprint.pformat(response.result)))
		else:
			logging.info("PushbulletTextNotify Success")

	def publishDoorState(self):
		"""
		Publish the state of the door to MQTT, if enabled
		"""
		if self.mqttEnabled:
			try:
				self.publish(self.state)
			except:
				self.logger.exception("door state publish failed")

	def cameraLoop(self):
		"""
		loop for camera picture taking - camera may have a delay built in which could cause monitorLoop to stall
		"""
		self.camera.capture()

		if self.pushbullet:
			notify = PushbulletImageNotify(self.pushbullet, self.camera.cameraFile)
			result = notify.result
			if 'error' in result.keys():
				for key in ['iden', 'sender_iden', 'receiver_iden']:
					try:
						del result[key]
					except KeyError:
						pass
				logging.info("PushbulletImageNotify Error:\n{}".format(pprint.pformat(result)))
			else:
				logging.info("PushbulletImageNotify Success")

		# endregion ThreadLoops
	# endregion Threading
	# region GPIO

	def setupGPIO(self):
		"""
		Set up GPIO for controlling & sensing door states
		"""
		self.gpioSettings = self.settings.gpio
		GPIO.setmode(GPIO.BCM)

		# initialize sesnsor
		# TODO: add ability to configure as pull-up or pull-down
		GPIO.setup(self.gpioSettings['pin_sensor'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.getState()

		# initialize control (relay
		GPIO.setup(self.gpioSettings['pin_control'], GPIO.OUT)
		# ensure control output is LOW
		self.off()
		
	def on(self):
		"""
		Set GPIO output HIGH for control pin
		"""
		self.logger.debug("control - on")
		GPIO.output(self.gpioSettings['pin_control'], GPIO.HIGH)
		
	def off(self):
		"""
		Set GPIO output LOW for control pin
		"""
		self.logger.debug("control - off")
		GPIO.output(self.gpioSettings['pin_control'], GPIO.LOW)
		
	def toggle(self):
		"""
		Toggle GPIO relay
		"""
		self.on()
		sleep(self.gpioSettings.get('relay_toggle_delay', 0.3))
		self.off()
		
	def getState(self):
		"""
		Get current state of GPIO input pin
		@rtype: bool
		"""
		return bool(GPIO.input(self.gpioSettings['pin_sensor']))

	# endregion GPIO
	# region MQTT

	def setupMQTT(self):
		"""
		Set up MQTT connection
		"""
		# topic subscription happens in on_connect
		self.logger.debug("setting up mqtt client connection")
		self.mqttEnabled = False
		try:
			self.clientControl = paho.Client(client_id=self.mqttSettings['client'])
			self.clientControl.on_connect = self.on_connect
			self.clientControl.on_subscribe = self.on_subscribe
			self.clientControl.on_message = self.on_message
			self.clientControl.on_publish = self.on_publish
			self.clientControl.connect(self.mqttSettings['broker'], self.mqttSettings['port'])
			self.logger.debug("mqtt client connected. client: {}. starting loop".format(str(self.clientControl)))
			self.clientControl.loop_start()
			self.mqttEnabled = True
			self.logger.debug("mqtt client loop started")
		except Exception as e:
			self.logger.exception("Exception while setting up MQTT client: {}".format(e))
		
	def publish(self, data):
		"""
		Publish data to MQTT state topic
		@param data: data to be published
		@type data: str
		"""
		self.logger.debug("mqtt: pub '{}' to topic '{}'".format(data, self.mqttSettings['topic_state']))
		try:
			pahopub.single(
				topic=self.mqttSettings['topic_state'],
				payload=str(data),
				qos=1,
				retain=True,
				hostname=self.mqttSettings['broker'],
				port=self.mqttSettings['port'],
				client_id=self.mqttSettings['client']
			)
		except Exception as e:
			self.logger.exception("mqtt: pub exception:\n{}".format(e))
			pass
		
	def on_connect(self, client, userdata, flags, rc):
		"""
		Catch MQTT connection events and subscribe to an MQTT topic for listening
		@param client: the MQTT client to use for subscribing to topics
		@param userdata: any special user data needed (currently unused but comes with connection call)
		@param flags: any flags for the connection (unused but comes with automatically)
		@param rc: result of connection
		"""
		self.logger.info("mqtt: (CONNECT) client {} received with code {}".format(client, rc))

		# check connection results
		# MQTTCLIENT_SUCCESS = 0, all others are some kind of error.
		if rc != 0:
			if rc == -4:
				self.logger.exception("mqtt: ERROR: 'too many messages'\n")
			elif rc == -5:
				self.logger.exception("mqtt: ERROR: 'invalid UTF-8 string'\n")
			elif rc == -9:
				self.logger.exception("mqtt: ERROR: 'bad QoS'\n")
			raise MQTTError("on_connect 'rc' failure")

		# no errors, subscribe to the MQTT topic
		self.logger.info("subscribing to topic: {}".format(self.mqttSettings['topic_control']))
		client.subscribe(self.mqttSettings['topic_control'], qos=1)
		
	def on_subscribe(self, client, userdata, mid, granted_qos):
		"""
		Event handler for when the client attempts to subscribe to a topic
		@param client: the MQTT client that subscribed to a topic
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: results of subscription
		@param granted_qos: quality of service granted to the connection
		"""
		self.logger.debug("mqtt: (SUBSCRIBE) client: {}, mid: {}, granted_qos: {}".format(client, mid, granted_qos))
		
	def on_publish(self, client, userdata, mid, rc):
		"""
		Event handler for when the client attempts to publish to a topic
		@param client: the MQTT client that published
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: result of connection
		@param rc: result of connection
		@return: None
		"""
		self.logger.debug("mqtt: (PUBLISH) client: {}, mid: {}".format(client, mid))
		
	def on_message(self, client, userdata, msg):
		"""
		Event handler for when client receives a message on the subscribed topic
		@param client: the client that received a message
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param msg: the received message
		"""
		self.logger.debug("mqtt: (MESSAGE) client: {}, topic: {}, QOS: {}, payload: {}".format(client, msg.topic, msg.qos, msg.payload))
		if msg.topic == self.mqttSettings.get('topic_control') and msg.payload in ["TOGGLE", "CLOSE"]:
			self.toggle()

	# endregion MQTT

	def __dummy(self):
		"""
		Workaround for PyCharm custom folding regions bug
		"""
		return