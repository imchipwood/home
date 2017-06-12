'''Threaded MQTT Door Control and State Monitoring

Chip Wood, Jan. 2017

This file is a one-stop shop for reading the state of a door as well as
controlling the door, through the use of two GPIO pins and an MQTT connection.

A state monitoring MQTT client thread reads the state sensor at 1Hz.
When the state changes, the new state is published on an MQTT topic.
The published states are "open" and "closed".

A separate control MQTT client thread subscribes to the control topic and
toggles the GPIO when a message is published with the payload of "TOGGLE".
It does not respond to any other messages.
'''
import logging
import RPi.GPIO as GPIO
import paho.mqtt.client as paho
import paho.mqtt.publish as pahopub
import timeit
from time import sleep
# from multiprocessing import Process
from threading import Thread
from cameraController import PiCameraController
from lib.services.pushbulletNotify import PushbulletImageNotify, PushbulletTextNotify
import traceback

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
	"""Threaded Door Controller object

	This class is intended to handle all aspects of door monitoring and control, as well as camera control

	Once instantiated, simply call the start() method to launch the threads
	"""
	def __init__(self, configFile, debug=False):
		# DoorController.__init__(self)
		super(DoorController, self).__init__()
		self.state = None

		# handle logging level
		self.logger = logging.getLogger(__name__)
		loggingLevel = logging.INFO
		if debug:
			loggingLevel = logging.DEBUG

		# logging level has to be set globally for some reason
		logging.getLogger().setLevel(loggingLevel)

		# read the config file - we need the log file path to finish setting up logging
		self.mqttSettings, self.gpioSettings, logFile, cameraEnabled, self.pushbullet = self.readConfig(configFile)

		# finish setting up logging
		self.setupLogging(loggingLevel=loggingLevel, logFile=logFile)

		# set up MQTT connections
		self.clientControl = None

		# create the camera
		if cameraEnabled:
			self.camera = PiCameraController(configFile=configFile, debug=debug)
		else:
			self.camera = None

		# setup sensing/controlling GPIO
		self.setupGPIO()

		self.monitor = True
		self.monitorThread = Thread(target=self.monitorLoop, args=[])
		# self.controlThread = Process(target=self.controlLoop, args=[self])

		self.logCurrentSetup()
		return

	def readConfig(self, configFile):
		"""Read the config file for MQTT, GPIO, and logging setup

		Expected tokens:
			log - full path of file to log to
			mqtt_client - name to send MQTT messages as
			mqtt_broker - IP address of MQTT broker
			mqtt_port - port to talk to MQTT broker on
			mqtt_topic_state - MQTT topic to send state updates on
			mqtt_topic_control - MQTT topic to listen for commands on
			gpio_pin_sensor - GPIO # that door is connected to
			gpio_pin_control - GPIO # that relay is connected to

		@param configFile: path to config file to parse
		@return: tuple (dict of mqtt settings, dict of gpio settings, str logfile path, bool cameraEnabled)
		"""
		mqttConfig = {}
		gpioConfig = {}
		logFile = None
		cameraEnabled = False
		pushbullet = False

		with open(configFile, "r") as inf:
			lines = inf.readlines()

		for line in lines:
			# skip commented out lines, blank lines, and lines without an = sign
			if line[0] == '#' or line[:2] == '//' or line == '\n' or '=' not in line:
				continue

			# line is good, split it by '=' to get token and value
			line = line.rstrip().split("=")
			key, val = line[:2]

			# try to convert the value to an int or float. some values will be strings so this won't work, but
			# it means we don't have to do the conversions elsewhere
			if '.' in val:
				try:
					val = float(val)
				except:
					pass
			else:
				try:
					val = int(val)
				except:
					pass

			# store values as appropriate
			if 'mqtt' in key:
				key = "_".join(key.split('_')[1:])
				mqttConfig[key] = val
			elif 'gpio' in key:
				key = "_".join(key.split('_')[1:])
				gpioConfig[key] = val
			elif key == 'log':
				logFile = val
			elif 'camera' in key:
				cameraEnabled = True
			elif 'pushbullet' in key:
				pushbullet = val

		return mqttConfig, gpioConfig, logFile, cameraEnabled, pushbullet

	def setupLogging(self, loggingLevel, logFile=None):
		"""Set up logging stream and file handlers

		@param loggingLevel: logging level as defined by logging package
		@param logFile: (optional) path for file logging
		@return: None
		"""
		if loggingLevel == logging.DEBUG:
			val = 'DEBUG'
		elif loggingLevel == logging.INFO:
			val = 'INFO'
		else:
			raise AttributeError("DoorController only supports logging.INFO and logging.DEBUG levels")
		logging.info("Logging level: {}".format(val))

		# stdout stream handler
		ch = logging.StreamHandler()
		ch.setLevel(loggingLevel)

		# stdout logging formatting
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)
		ch.setFormatter(stdoutFormatter)
		self.logger.addHandler(ch)

		# set up file handler logger
		if logFile:
			fh = logging.FileHandler(logFile)
			fh.setLevel(logging.DEBUG)

			# file logging formatting
			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fh.setFormatter(fileFormatter)
			self.logger.addHandler(fh)
		return

	def logCurrentSetup(self):
		"""Write the current setup to the debug stream

		@return: None
		"""
		self.logger.debug("\n----------------------------------------")

		# MQTT settings
		s = ''
		for key, val in self.mqttSettings.items():
			s += '{}: {}\n'.format(key, val)
		self.logger.debug("\nMQTT Settings:\n{}".format(s))

		# GPIO settings
		s = ''
		for key, val in self.gpioSettings.items():
			s += '{}: {}\n'.format(key, val)
		self.logger.debug("\nGPIO Settings:\n{}".format(s))

		# camera
		self.logger.debug("Camera enabled: {}\n".format(self.camera))

		# notifications
		self.logger.debug("Notifications enabled: {}\n".format(True if self.pushbullet else False))

		self.logger.debug("----------------------------------------\n")

		return

###############################################################################

	'''Start the state monitoring and control threads
	This function initializes all MQTT connections and subscriptions
	and launches separate Processes for each
	'''
	def start(self):
		"""Start the state monitoring thread and launch the MQTT connections

		@return: None
		"""

		# begin control loop
		self.setupMQTT()

		sleep(2)

		# launch monitor thread
		try:
			self.logger.debug("starting state thread")
			self.monitorThread.start()
		except:
			self.logger.exception("failed to start state thread")
			self.cleanup()
			raise

		# sleep(2)

		# # launch control thread
		# try:
		# 	self.logger.debug("starting control thread")
		# 	self.controlThread.start()
		# except:
		# 	self.logger.exception("failed to start control thread")
		# 	self.cleanup()
		# 	raise
		
		return

	def cleanup(self):
		"""Clean up all threads and GPIO

		@return:
		"""
		self.logger.info("cleaning up")

		try:
			self.logger.debug("shutting down monitor loop")
			# self.monitorThread.terminate()
			# self.monitorThread.loop_stop()
			# self.monitorThread.unsubscribe(self.mqttSettings['topic_state'])()
			# self.monitorThread.disconnect()
			self.monitor = False
		except Exception as e:
			self.logger.exception("Exception while shutting down monitor loop: {}".format(e))
			traceback.print_exc()
			pass

		try:
			self.logger.debug("shutting down control thread")
			# self.controlThread.terminate()
			self.clientControl.loop_stop()
			self.clientControl.unsubscribe(self.mqttSettings['topic_control'])
			self.clientControl.disconnect()
		except Exception as e:
			self.logger.exception("Exception while shutting down control loop: {}".format(e))
			traceback.print_exc()
			pass

		try:
			self.logger.debug("Cleaning up GPIO")
			GPIO.cleanup()
		except Exception as e:
			self.logger.exception("Exception while cleaning up GPIO: {}".format(e))
			traceback.print_exc()
			pass

		if self.camera:
			try:
				self.logger.debug("Cleaning up camera")
				self.camera.cleanup()
			except Exception as e:
				self.logger.exception("Exception while cleaning up camera: {}".format(e))
				traceback.print_exc()
				pass

		return

###############################################################################
# GPIO interactions

	def setupGPIO(self):
		"""Set up GPIO for controlling & sensing door states

		@return: None
		"""
		GPIO.setmode(GPIO.BCM)

		# initialize sesnsor
		# TODO: add ability to configure as pull-up or pull-down
		GPIO.setup(self.gpioSettings['pin_sensor'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self.getState()

		# initialize control (relay
		GPIO.setup(self.gpioSettings['pin_control'], GPIO.OUT)
		# ensure control output is LOW
		self.off()
		return

	def on(self):
		"""set GPIO output HIGH for control pin

		@return: None
		"""
		self.logger.debug("control - on")
		GPIO.output(self.gpioSettings['pin_control'], GPIO.HIGH)
		return

	def off(self):
		"""set GPIO output LOW for control pin

		@return: None
		"""
		self.logger.debug("control - off")
		GPIO.output(self.gpioSettings['pin_control'], GPIO.LOW)
		return

	def toggle(self):
		"""toggle GPIO relay

		@return: None
		"""
		self.on()
		if 'relay_toggle_delay' in self.gpioSettings.keys():
			sleep(self.gpioSettings['relay_toggle_delay'])
		else:
			sleep(0.3)
		self.off()
		return

	def getState(self):
		"""Get current state of GPIO input pin

		@return: int
		"""
		return GPIO.input(self.gpioSettings['pin_sensor'])

###############################################################################
# looping functions - these two functions are intended to be launched in individual threads

	def controlLoop(self):
		"""Start the MQTT client

		@return:
		"""
		# begin control loop
		try:
			self.logger.debug("control loop")
			# self.clientControl.loop_forever()  # blocking
			self.clientControl.loop()  # non-blocking
		except:
			# clean up in case of emergency
			try:
				self.logger.debug("clientControl cleaning up")
				self.clientControl.loop_stop()
				self.clientControl.unsubscribe(self.mqttSettings['topic_control'])
				self.clientControl.disconnect()
			except:
				self.logger.exception("clientControl cleanup exception")
				raise
		return

	def monitorLoop(self):
		"""Monitor the door open/closed sensor @1Hz

		@remark: set DoorController.monitor=False to stop the thread

		@return: None
		"""
		oneHz = 1.0
		lastOneHzTime = 0
		lastDoorState = None

		while self.monitor:
			now = float(timeit.default_timer())

			if (now - lastOneHzTime) > oneHz:
				lastOneHzTime = now

				try:
					newState = self.getState()

					if newState != lastDoorState:
						self.state = newState
						self.logger.debug("monitor state: %s" % (self.state))

						# TODO: add ability to configure N.O. vs N.C.

						self.publish(self.state)

						if self.pushbullet and lastDoorState is not None:
							text = "Garage Door {}".format('open' if self.state else 'closed')
							PushbulletTextNotify(self.pushbullet, text, text)

						if self.camera and self.state and lastDoorState is not None:
							self.camera.capture()

							if self.pushbullet:
								PushbulletImageNotify(self.pushbullet, self.camera.cameraFile)

						lastDoorState = newState

				except:
					self.logger.exception("state exception")
					raise

		self.logger.info("Monitor loop exiting")
		return

###############################################################################
# Connection and cleanup functions

###############################################################################
# MQTT interaction functions

	def setupMQTT(self):
		"""Set up MQTT connection

		@return: None
		"""
		# topic subscription happens in on_connect
		self.logger.debug("setting up mqtt client connection")
		try:
			self.clientControl = paho.Client(client_id=self.mqttSettings['client'])
			self.clientControl.on_connect = self.on_connect
			self.clientControl.on_subscribe = self.on_subscribe
			self.clientControl.on_message = self.on_message
			self.clientControl.on_publish = self.on_publish
			self.clientControl.connect(self.mqttSettings['broker'], self.mqttSettings['port'])
			self.logger.debug("mqtt client connected. client: {}. starting loop".format(str(self.clientControl)))
			self.clientControl.loop_start()
			self.logger.debug("mqtt client loop started")
		except Exception as e:
			self.logger.exception("Exception while setting up MQTT client: {}".format(e))
			traceback.print_exc()
			raise
		return

	def publish(self, data):
		"""Publish data to MQTT state topic

		@param data: data to be published
		@return: None
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
		return

	def on_connect(self, client, userdata, flags, rc):
		"""Catch MQTT connection events and subscribe to an MQTT topic for listening

		@param client: the MQTT client to use for subscribing to topics
		@param userdata: any special user data needed (currently unused but comes with connection call)
		@param flags: any flags for the connection (unused but comes with automatically)
		@param rc: result of connection
		@return: None
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
		return

	def on_subscribe(self, client, userdata, mid, granted_qos):
		"""Event handler for when the client attempts to subscribe to a topic

		@param client: the MQTT client that subscribed to a topic
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: results of subscription
		@param granted_qos: quality of service granted to the connection
		@return:
		"""
		self.logger.debug("mqtt: (SUBSCRIBE) client: {}, mid: {}, granted_qos: {}".format(client, mid, granted_qos))
		return

	def on_publish(self, client, userdata, mid, rc):
		"""Event handler for when the client attempts to publish to a topic

		@param client: the MQTT client that published
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: result of connection
		@param rc: result of connection
		@return: None
		"""
		self.logger.debug("mqtt: (PUBLISH) client: {}, mid: {}".format(client, mid))
		return

	def on_message(self, client, userdata, msg):
		"""Event handler for when client receives a message on the subscribed topic

		@param client: the client that received a message
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param msg: the received message
		@return:
		"""
		self.logger.debug("mqtt: (MESSAGE) client: {}, topic: {}, QOS: {}, payload: {}".format(client, msg.topic, msg.qos, msg.payload))
		if msg.topic == self.mqttSettings['topic_control'] and msg.payload in ["TOGGLE", "CLOSE"]:
			self.toggle()
		return
