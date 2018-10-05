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
from threading import Thread

from library.config.doorConfig import DoorConfig
from library.config.pushbulletConfig import PushbulletConfig
from cameraController import PiCameraController
from library.services.pushbulletNotify import PushbulletImageNotify, PushbulletTextNotify


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
		self.debug = debug
		self.state = None

		# initalize logger
		self.logger = logging.getLogger(__name__)
		self.logger.info("Logger initialized")

		# logging level has to be set globally for some reason
		logging.getLogger().setLevel(logging.DEBUG)

		# read the config files
		self.gpio = None
		""" @type: library.config.doorConfig.DoorGPIOConfiguration """
		self.settings = DoorConfig(doorConfigFile)

		# finish setting up logging
		self.setupLogging(skipLogging=skipLogging, loggingLevel=self.debug, logFile=self.settings.log)

		# create the camera
		self.camera = self.setupCamera(cameraConfigFile)

		self.pushbulletConfig, self.pushbullet = self.setupNotifications(pushbulletConfigFile)

		# set up MQTT connections
		self.clientControl = None

		# setup sensing/controlling GPIO
		self.setupGPIO()

		self.monitor = False
		self.monitorThread = Thread(target=self.monitorLoop, args=[])

		self.logCurrentSetup()

	def __repr__(self):
		"""
		@rtype: str
		"""
		return "Open" if self.open else "Closed"

	@property
	def open(self):
		"""
		Check if door is open
		@return: whether or not door is open
		@rtype: bool
		"""
		return self.state
	
	@property
	def mqtt(self):
		"""
		@rtype: library.config.doorConfig.DoorMQTTConfiguration
		"""
		return self.settings.mqtt

	# region Logging

	def setupLogging(self, skipLogging=False, loggingLevel=False, logFile=None):
		"""
		Set up logging stream and file handlers
		@param skipLogging: Flag to disable logging enhancements
		@type skipLogging: bool
		@param loggingLevel: logging level as defined by logging package
		@type loggingLevel: int
		@param logFile: (optional) path for file logging
		@type logFile: str
		"""
		if skipLogging:
			# Do nothing
			return

		self.logger.info("Logging level: {}".format('DEBUG' if loggingLevel else 'INFO'))

		# stdout stream handler
		streamHandler = logging.StreamHandler()
		streamHandler.setLevel(logging.DEBUG if loggingLevel else logging.INFO)

		# stdout logging formatting
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)
		streamHandler.setFormatter(stdoutFormatter)

		# remove existing handlers then add the new one
		self.logger.handlers = []
		self.logger.addHandler(streamHandler)

		# set up file handler logger - always debug level
		if logFile:
			self.logger.info("Logging to file: {}".format(logFile))
			fileHandler = logging.FileHandler(logFile)
			fileHandler.setLevel(logging.DEBUG)

			# file logging formatting
			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fileHandler.setFormatter(fileFormatter)
			self.logger.addHandler(fileHandler)
		else:
			self.logger.warning("No log file path specified - file logging disabled")
		
	def logCurrentSetup(self):
		"""
		Write the current setup to the debug stream
		"""
		self.logger.debug("----------------------------------------")
		self.logger.debug("\nMQTT Settings:\n{}".format(str(self.mqtt)))
		self.logger.debug("\nGPIO Settings:\n{}".format(self.gpio))
		self.logger.debug("Camera enabled: {}".format(bool(self.camera)))
		self.logger.debug("Notifications enabled: {}".format(bool(self.pushbullet)))
		self.logger.debug("----------------------------------------")

	# endregion Logging
	# region Setup

	def setupCamera(self, configFile):
		"""
		Set up the camera if we have a config file
		@param configFile: path to camera config file
		@type configFile: str
		@return: camera controller
		@rtype: PiCameraController or None
		"""
		if configFile is not None:
			return PiCameraController(configFile=configFile, debug=self.debug)
		return None

	def setupNotifications(self, configFile):
		"""
		Set up notifications
		@param configFile: path to config file
		@type configFile: str
		@return: tuple of config & API key
		@rtype: tuple(PushbulletConfig, str) or tuple(None, None)
		"""
		if configFile is not None:
			config = PushbulletConfig(configFile)
			return config, config.apiKey
		return None, None

	# endregion Setup
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
			self.logger.exception("door control loop failed to initialize - will not be able to control door")

		sleep(2)

		# launch monitor thread
		if self.canSenseDoor():
			try:
				self.logger.debug("starting state thread")
				self.monitor = True
				self.monitorThread.start()
			except:
				self.logger.exception("Failed to start door state monitoring thread!")
				self.cleanup()
				raise
		else:
			self.logger.warning("Cannot start door monitoring thread - GPIO pin # missing!")
		
	def cleanup(self):
		"""
		Clean up all threads and GPIO
		"""
		self.logger.info("cleaning up")

		try:
			self.logger.debug("shutting down monitor loop")
			self.monitor = False
		except:
			self.logger.exception("Exception while shutting down door state monitoring loop")

		if self.clientControl:
			try:
				self.logger.debug("shutting down control thread")
				self.clientControl.loop_stop()
				# self.clientControl.unsubscribe(self.mqtt.topicControl)
				self.clientControl.disconnect()
			except:
				self.logger.exception("Exception while shutting down MQTT door control loop")

		try:
			self.logger.debug("Cleaning up GPIO")
			GPIO.cleanup()
		except:
			self.logger.exception("Exception while cleaning up GPIO")

		if self.camera:
			try:
				self.logger.debug("Cleaning up camera")
				self.camera.cleanup()
			except:
				self.logger.exception("Exception while cleaning up camera")

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
					self.logger.exception("Door state monitor loop exception")
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
				self.logPushbulletErrors(notify)
			else:
				self.logger.info("Door Opened, skipping text notify")

		if self.camera and self.open and lastDoorState is not None:
			# create a separate thread for the camera so this loop can continue running while camera operates
			t = Thread(target=self.cameraLoop, args=[])
			t.start()

		return newState

	def logPushbulletErrors(self, response):
		if 'error' in response.result:
			for key in ['iden', 'sender_iden', 'receiver_iden']:
				del response.result[key]
			self.logger.error("PushbulletTextNotify Error:\n{}".format(pprint.pformat(response.result)))
		else:
			self.logger.info("PushbulletTextNotify Success")

	def canPublishState(self):
		"""
		Check if it's possible to publish the door state to an MQTT topic
		@return:
		@rtype: bool
		"""
		requirements = {
			'client': self.mqtt.client,
			'broker': self.mqtt.broker,
			'topicState': self.mqtt.topicState,
			'port': self.mqtt.port
		}
		return all([val not in [None, ''] for val in requirements.itervalues()])

	def getMissingPublishRequirements(self):
		"""
		Get a list of the MQTT attributes preventing publishing state information
		@return: list of MQTT attributes
		@rtype: list[str]
		"""
		requirements = {
			'client': self.mqtt.client,
			'broker': self.mqtt.broker,
			'topicState': self.mqtt.topicState,
			'port': self.mqtt.port
		}
		return [key for key, val in requirements.iteritems() if val in [None, '']]

	def publishDoorState(self):
		"""
		Publish the state of the door to MQTT
		"""
		if self.canPublishState():
			try:
				self.publish(str(self))
			except:
				self.logger.exception("MQTT: Failed to publish door state!")
		else:
			self.logger.info(
				"Cannot publish state to MQTT - missing MQTT attributes: {}".format(
					", ".join(self.getMissingPublishRequirements())
				)
			)

	def cameraLoop(self):
		"""
		loop for camera picture taking - camera may have a delay built in which could cause monitorLoop to stall
		"""
		self.camera.capture()

		if self.pushbullet:
			notify = PushbulletImageNotify(self.pushbullet, self.camera.cameraFile)
			result = notify.result
			if 'error' in result:
				for key in ['iden', 'sender_iden', 'receiver_iden']:
					try:
						del result[key]
					except KeyError:
						pass
				self.logger.error("PushbulletImageNotify Error:\n{}".format(pprint.pformat(result)))
			else:
				self.logger.info("PushbulletImageNotify Success")

		# endregion ThreadLoops
	# endregion Threading
	# region GPIO

	def setupGPIO(self):
		"""
		Set up GPIO for controlling & sensing door states
		"""
		self.gpio = self.settings.gpio
		GPIO.setmode(GPIO.BCM)

		# TODO: add ability to configure as pull-up or pull-down
		if self.canSenseDoor():
			GPIO.setup(self.gpio.pinSensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			self.getState()
		else:
			self.logger.warning("GPIO door state monitoring disabled - missing GPIO pin #")

		if self.canControlDoor():
			GPIO.setup(self.gpio.pinControl, GPIO.OUT)
			# ensure control output is LOW
			self.off()
		else:
			self.logger.warning("GPIO door control disabled - missing GPIO pin # or MQTT info")
		
	def on(self):
		"""
		Set GPIO output HIGH for control pin
		"""
		self.logger.debug("control - on")
		GPIO.output(self.gpio.pinControl, GPIO.HIGH)
		
	def off(self):
		"""
		Set GPIO output LOW for control pin
		"""
		self.logger.debug("control - off")
		GPIO.output(self.gpio.pinControl, GPIO.LOW)
		
	def toggle(self):
		"""
		Toggle GPIO relay
		"""
		self.on()
		sleep(self.gpio.relayToggleDelay)
		self.off()
		
	def getState(self):
		"""
		Get current state of GPIO input pin
		@rtype: bool or None
		"""
		if not self.canSenseDoor():
			return None
		return bool(GPIO.input(self.gpio.pinSensor))

	def canSenseDoor(self):
		"""
		Check if we can sense the door
		@rtype: bool
		"""
		return self.gpio.pinSensor is not None

	# endregion GPIO
	# region MQTT

	def canControlDoor(self):
		"""
		Check if it's possible to publish the door state to an MQTT topic
		@return:
		@rtype: bool
		"""
		requirements = {
			'client': self.mqtt.client,
			'broker': self.mqtt.broker,
			'topicControl': self.mqtt.topicControl,
			'port': self.mqtt.port
		}
		return all([val not in [None, ''] for val in requirements.itervalues()]) and self.gpio.pinControl is not None

	def setupMQTT(self):
		"""
		Set up MQTT connection
		"""
		if self.canControlDoor():
			# topic subscription happens in on_connect - no need to call it here
			self.logger.debug("setting up mqtt client connection")
			try:
				# Initialize the client
				self.clientControl = paho.Client(client_id=self.mqtt.client)

				# Setup callbacks
				self.clientControl.on_connect = self.on_connect
				self.clientControl.on_subscribe = self.on_subscribe
				self.clientControl.on_message = self.on_message
				self.clientControl.on_publish = self.on_publish

				# Attempt connection and begin the loop
				self.clientControl.connect(self.mqtt.broker, self.mqtt.port)
				self.logger.debug(
					"mqtt client connected. client: {}. starting loop".format(self.clientControl._client_id)
				)
				self.clientControl.loop_start()

				self.logger.debug("mqtt client loop started")
			except:
				self.logger.exception("MQTT: Exception while initializing control loop!")
		else:
			self.logger.info("Missing information for door control MQTT setup - skipping")
		
	def publish(self, data):
		"""
		Publish data to MQTT state topic
		@param data: data to be published
		@type data: str
		"""
		self.logger.debug("mqtt: pub '{}' to topic '{}'".format(data, self.mqtt.topicState))
		try:
			pahopub.single(
				topic=self.mqtt.topicState,
				payload=str(data),
				qos=1,
				retain=True,
				hostname=self.mqtt.broker,
				port=self.mqtt.port,
				client_id=self.mqtt.client
			)
		except:
			self.logger.exception("MQTT: pub exception!")
		
	def on_connect(self, client, userdata, flags, rc):
		"""
		Catch MQTT connection events and subscribe to an MQTT topic for listening
		@param client: the MQTT client to use for subscribing to topics
		@param userdata: any special user data needed (currently unused but comes with connection call)
		@param flags: any flags for the connection (unused but comes with automatically)
		@param rc: result of connection
		"""
		self.logger.info("mqtt: (CONNECT) client {} received with code {}".format(client._client_id, rc))

		# check connection results
		# MQTTCLIENT_SUCCESS = 0, all others are some kind of error.
		if rc != 0:
			exceptionMap = {
				-4: 'too many messages',
				-5: 'invalid UTF-8 string',
				-9: 'bad QoS'
			}
			self.logger.exception("mqtt: ERROR: rc={}, {}\n".format(rc, exceptionMap.get(rc)))
			raise MQTTError("on_connect 'rc' failure")

		# no errors, subscribe to the MQTT topic
		self.logger.info("subscribing to topic: {}".format(self.mqtt.topicControl))
		client.subscribe(self.mqtt.topicControl, qos=1)
		
	def on_subscribe(self, client, userdata, mid, granted_qos):
		"""
		Event handler for when the client attempts to subscribe to a topic
		@param client: the MQTT client that subscribed to a topic
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: results of subscription
		@param granted_qos: quality of service granted to the connection
		"""
		self.logger.debug("mqtt: (SUBSCRIBE) client: {}, mid: {}, granted_qos: {}".format(client._client_id, mid, granted_qos))
		
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
		if msg.topic == self.mqtt.get('topic_control') and msg.payload in ["TOGGLE", "CLOSE"]:
			self.toggle()

	# endregion MQTT

	def __dummy(self):
		"""
		Workaround for PyCharm custom folding regions bug
		"""
		return
