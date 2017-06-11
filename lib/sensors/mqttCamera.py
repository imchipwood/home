import logging
import traceback
import ephem
from time import sleep
import paho.mqtt.client as paho
from picamera import PiCamera
from lib.services.pushbulletNotify import PushbulletImageNotify

# hass mqtt publish service data for testing:
# { "topic": "home-assistant/garage/cameraControl", "payload": "CAPTURE", "qos": "1", "retain": "false" }


class MQTTError(BaseException):
	pass


class MqttCamera(object):
	def __init__(self, configFile, debug=False):
		# super(MqttCamera, self).__init__()
		# set up logging first
		self.logger = logging.getLogger(__name__)

		# formatting - add this to logging handler
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)

		# handle logging level
		loggingLevel = logging.INFO
		if debug:
			loggingLevel = logging.DEBUG

		logging.getLogger().setLevel(loggingLevel)
		if loggingLevel == logging.DEBUG:
			val = 'DEBUG'
		else:
			val = 'INFO'
		logging.info("Logging level: {}".format(val))

		# stdout stream handler
		ch = logging.StreamHandler()
		# ch.setLevel(loggingLevel)
		ch.setLevel(loggingLevel)
		ch.setFormatter(stdoutFormatter)
		self.logger.addHandler(ch)

		# attempt to parse the config file
		self.cameraSettings, self.mqttSettings, self.pushbulletSettings, self.logFile = self.parseConfig(configFile)

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
		self.setupCamera()

		self.clientControl = None
		return
	
	def setupCamera(self):
		"""Set up the PiCamera based on settings found in config file

		@return: None
		"""
		self.logger.debug("setupCamera")
		self.logger.debug(self.cameraSettings)
		self.camera = PiCamera()
		cameraSettingsKeys = self.cameraSettings.keys()

		if 'camera_rotation' in cameraSettingsKeys:
			self.camera.rotation = self.cameraSettings['camera_rotation']

		if 'camera_brightness' in cameraSettingsKeys:
			self.camera.brightness = self.cameraSettings['camera_brightness']

		if 'camera_contrast' in cameraSettingsKeys:
			self.camera.contrast = self.cameraSettings['camera_contrast']

		if 'camera_resolution' in cameraSettingsKeys:
			width, height = [int(x) for x in self.cameraSettings['camera_resolution'].split(',')]
			self.logger.debug("setting camera resolution to width, height: {}, {}".format(width, height))
			self.camera.resolution = (width, height)

		if 'camera_filepath' in cameraSettingsKeys:
			self.cameraFile = self.cameraSettings['camera_filepath']
		else:
			raise IOError("No specified filepath for camera found in config file")

		# set the ISO based on whether or not the sun is up
		self.updateCameraISO()
		
		self.camera.start_preview()
		return

	def updateCameraISO(self):
		sun = ephem.Sun()
		sea = ephem.city("Seattle")
		sun.compute(sea)
		twilight = -12 * ephem.degree
		daytime = sun.alt < twilight

		if 'camera_iso_daytime' in self.cameraSettings.keys():
			daytimeISO = self.cameraSettings['camera_iso_daytime']
		else:
			daytimeISO = 200

		if 'camera_iso_nighttime' in self.cameraSettings.keys():
			nighttimeISO = self.cameraSettings['camera_iso_nighttime']
		else:
			nighttimeISO = 800

		iso = daytimeISO
		if not daytime:
			iso = nighttimeISO

		self.logger.debug("setting camera ISO to {}".format(iso))
		self.camera.iso = iso
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
		self.logger.info("cleaning up")

		try:
			self.logger.debug("terminating control thread")
			self.clientControl.loop_stop()
			self.logger.debug("control thread terminated")
		except Exception as e:
			self.logger.exception("exception while trying to terminate thread: {}".format(e))
			traceback.print_exc()
			pass

		try:
			self.logger.debug("disabling camera")
			self.camera.stop_preview()
			self.logger.debug("camera disabled")
		except:
			pass

		return

	def start(self):
		"""Start threads

		@return: None
		"""
		try:
			self.logger.info("starting MQTT client")
			self.clientControl = paho.Client(client_id=self.mqttSettings['mqtt_client'])
			self.clientControl.on_connect = self.on_connect
			self.clientControl.on_subscribe = self.on_subscribe
			self.clientControl.on_message = self.on_message
			self.clientControl.connect(self.mqttSettings['mqtt_broker'], self.mqttSettings['mqtt_port'])
			self.logger.debug("starting mqtt loop")
			self.clientControl.loop_start()

		except:
			self.logger.exception("failed to start control thread")
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
		self.logger.info("mqtt: (CONNECTION) received with code {}".format(rc))

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
		return

	def on_message(self, client, userdata, msg):
		"""Event handler for when client receives a message on the subscribed topic

		@param client: the client that received a message
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param msg: the received message
		@return:
		"""
		self.logger.info("mqtt: (RX) topic: {}, QOS: {}, payload: {}".format(msg.topic, msg.qos, msg.payload))

		# check the topic & payload to see if we should respond something
		if msg.topic == self.mqttSettings['mqtt_topic_control'] and msg.payload == 'CAPTURE':
			if 'camera_delay' in self.cameraSettings.keys():
				cameraDelay = self.cameraSettings['camera_delay']
			else:
				cameraDelay = 10

			# update the camera ISO based on the time of day in case the thread has been running for long enough
			# for the sun to have gone down or come up again
			self.updateCameraISO()

			# sleep a little bit to let the garage door open enough that there's some light
			self.logger.info("taking picture in {} seconds: {}".format(cameraDelay, self.cameraFile))
			sleep(cameraDelay)

			# take the picture
			self.camera.capture(self.cameraFile)

			# send the picture if we have pushbullet settings
			if 'pushbullet_api' in self.pushbulletSettings.keys():
				self.logger.info("sending notification")
				PushbulletImageNotify(self.pushbulletSettings['pushbullet_api'], self.cameraFile)
				self.logger.info("notification sent")

		return
