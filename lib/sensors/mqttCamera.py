import logging
import traceback
from time import sleep
import paho.mqtt.client as paho
from picamera import PiCamera
from lib.services.pushbulletNotify import PushbulletImageNotify


class MQTTError(BaseException):
	pass


class MqttCamera(object):
	def __init__(self, configFile, debug=False):
		# super(MqttCamera, self).__init__()
		print("mqttCamera init")
		# set up logging first
		self.logger = logging.getLogger()

		# formatting - add this to logging handler
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)

		# stdout handler
		ch = logging.StreamHandler()
		loggingLevel = logging.INFO
		if debug:
			loggingLevel = logging.DEBUG
			print("Logging level: DEBUG")
		else:
			print("Logging level: INFO")
		ch.setLevel(loggingLevel)
		ch.setFormatter(stdoutFormatter)
		self.logger.addHandler(ch)

		# attempt to parse the config file
		cameraSettings, self.mqttSettings, self.pushbulletSettings, self.logFile = self.parseConfig(configFile)

		# set up file handler logger
		if self.logFile:
			fh = logging.FileHandler(self.logFile)
			fh.setLevel(logging.DEBUG)

			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fh.setFormatter(fileFormatter)
			self.logger.addHandler(fh)

		self.cameraFile = None
		self.camera = None
		self.setupCamera(cameraSettings)

		self.clientControl = None
		return
	
	def setupCamera(self, cameraSettingsDict):
		"""Set up the PiCamera based on settings found in config file
		
		@param cameraSettingsDict: 
		@return: 
		"""
		print("setupCamera")
		self.camera = PiCamera()
		cameraSettingsKeys = cameraSettingsDict.keys()

		if 'camera_rotation' in cameraSettingsKeys:
			self.camera.rotation = cameraSettingsDict['camera_rotation']

		if 'camera_brightness' in cameraSettingsKeys:
			self.camera.brightness = cameraSettingsDict['camera_brightness']

		if 'camera_contrast' in cameraSettingsKeys:
			self.camera.contrast = cameraSettingsDict['camera_contrast']

		if 'camera_filepath' in cameraSettingsKeys:
			self.cameraFile = cameraSettingsDict['camera_filepath']
		else:
			raise IOError("No specified filepath for camera found in config file")
		
		self.camera.start_preview()
		return

	def parseConfig(self, cfgFile):
		"""Parse a config file for relevant camera, MQTT, and logging info

		@param cfgFile: The file to parse
		@return: tuple of camera settings dict, mqtt settings dict, pushbullet settings dict, and str log file path
		"""
		cameraSettings = {}
		mqttSettings = {}
		pushbulletSettings = {}
		logFile = None

		with open(cfgFile, 'r') as inf:
			lines = inf.readlines()

		for line in lines:
			# skip commented out lines, blank lines, and lines without an = sign
			if line[0] == '#' or line[:2] == '//' or line == '\n' or '=' not in line:
				continue

			# line is good, split it by '=' to get token and value
			line = line.rstrip().split("=")
			key, val = line[:2]

			# try to convert the value to an int. some values will be strings so this won't work, but
			# it means we don't have to do the conversions elsewhere
			try:
				val = int(val)
			except:
				pass

			# decide what kind of setting we stumbled across
			if 'camera' in key:
				cameraSettings[key] = val
			elif 'mqtt' in key:
				mqttSettings[key] = val
			elif 'pushbullet' in key:
				pushbulletSettings[key] = val
			elif key == 'log':
				logFile = val

		return cameraSettings, mqttSettings, pushbulletSettings, logFile

	def cleanup(self):
		"""Attempt to gracefully exit the program

		@return: None
		"""
		print("cleaning up")

		try:
			print("terminating control thread")
			#self.controlThread.terminate()
			self.clientControl.loop_stop()
			print("control thread terminated")
		except Exception as e:
			print("exception while trying to terminate thread: {}".format(e))
			traceback.print_exc()
			pass

		try:
			print("disabling camera")
			self.camera.stop_preview()
			print("camera disabled")
		except:
			pass

		return

	def start(self):
		"""Start threads

		@return: None
		"""
		try:
			self.logger.debug("starting control thread")
			print("starting control thread")
			# self.controlThread.start()

			self.clientControl = paho.Client(client_id=self.mqttSettings['mqtt_client'])
			self.clientControl.on_connect = self.on_connect
			self.clientControl.on_subscribe = self.on_subscribe
			self.clientControl.on_message = self.on_message
			self.clientControl.connect(self.mqttSettings['mqtt_broker'], self.mqttSettings['mqtt_port'])
			print("starting mqtt loop")
			self.clientControl.loop_start()

		except:
			self.logger.exception("failed to start control thread")
			print("failed to start control thread")
			self.cleanup()
			raise
		return

	###############################################################################
	# MQTT interaction functions

	def on_connect(self, client, userdata, flags, rc):
		"""Catch MQTT connection events and subscribe to an MQTT topic for listening

		@param client: the MQTT client to use for subscribing to topics
		@param userdata: any special user data needed (currently unused but comes with connection call)
		@param flags: any flags for the connection (unused but comes with automatically)
		@param rc: result of connection
		@return: None
		"""
		self.logger.debug("mqtt: (CONNECTION) received with code {}".format(rc))
		print("mqtt: (CONNECTION) received with code {}".format(rc))

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
		client.subscribe(self.mqttSettings['mqtt_topic_control'], qos=1)
		return

	def on_subscribe(self, client, userdata, mid, granted_qos):
		"""Event handler for when the client attempts to subscribe to a topic

		@param client: the MQTT client that subscribed to a topic
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: results of subscription
		@param granted_qos: quality of service granted to the connection
		@return:
		"""
		self.logger.debug("mqtt: (SUBSCRIBE) mid: {}, granted_qos: {}".format(mid, granted_qos))
		print("mqtt: (SUBSCRIBE) mid: {}, granted_qos: {}".format(mid, granted_qos))
		return

	def on_message(self, client, userdata, msg):
		"""Event handler for when client receives a message on the subscribed topic

		@param client: the client that received a message
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param msg: the received message
		@return:
		"""
		self.logger.debug("mqtt: (RX) topic: {}, QOS: {}, payload: {}".format(msg.topic, msg.qos, msg.payload))
		print("mqtt: (RX) topic: {}, QOS: {}, payload: {}".format(msg.topic, msg.qos, msg.payload))

		# check the topic & payload to see if we should respond something
		if msg.topic == self.mqttSettings['mqtt_topic_control'] and msg.payload == 'CAPTURE':
			# sleep a little bit to let the garage door open enough that there's some light
			print("taking picture in 5 seconds: {}".format(self.cameraFile))
			sleep(5)
			self.camera.capture(self.cameraFile)
			if 'pushbullet_api' in self.pushbulletSettings.keys():
				print("sending notification")
				PushbulletImageNotify(self.pushbulletSettings['pushbullet_api'], self.cameraFile)
				print("notification sent")

		return
