
import logging
#from time import sleep
import paho.mqtt.client as paho
import paho.mqtt.publish as pahopub
from picamera import PiCamera
# from multiprocessing import Process
from threading import Thread

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
		cameraSettings, self.mqttSettings, self.logFile = self.parseConfig(configFile)

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
		#self.controlThread = Process(target=self.control, args=[])
		self.controlThread = Thread(target=self.control, args=[])
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
		@return: tuple of camera settings dict, mqtt settings dict, and str log file path
		"""
		cameraSettings = {}
		mqttSettings = {}
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
			elif key == 'log':
				logFile = val

		# debug stuff
		s = 'Camera settings:\n'
		for key, val in cameraSettings.items():
			s += "{}: {}\n".format(key, val)
		logging.debug(s)
		print(s)
		s = 'MQTT settings:\n'
		for key, val in mqttSettings.items():
			s += "{}: {}\n".format(key, val)
		logging.debug(s)
		print(s)

		return cameraSettings, mqttSettings, logFile

	def cleanup(self):
		"""Attempt to gracefully exit the program

		@return: None
		"""
		print("cleaning up")

		try:
			print("terminating control thread")
			self.controlThread.terminate()
			print("control thread terminated")
		except:
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
			self.logger.debug("start control thread")
			print("start control thread")
			self.controlThread.start()
		except:
			self.logger.exception("failed to start control thread")
			print("failed to start control thread")
			self.cleanup()
			raise
		return

	def control(self):
		"""Create an MQTT client, connect to the broker and subscribe to a thread. Loop forever waiting for messages

		@return: None
		"""
		self.clientControl = paho.Client(client_id=self.mqttSettings['mqtt_client'])
		self.clientControl.on_connect = self.on_connect
		self.clientControl.on_subscribe = self.on_subscribe
		self.clientControl.on_message = self.on_message
		self.clientControl.connect(self.mqttSettings['mqtt_broker'], self.mqttSettings['mqtt_port'])
		# begin control loop
		try:
			self.logger.debug("control loop_forever")
			print("control loop_forever")
			self.clientControl.loop_forever()  # blocking
		except:
			# clean up in case of emergency
			try:
				self.logger.debug("clientControl cleaning up")
				print("clientControl cleaning up")
				self.clientControl.loop_stop()
				self.clientControl.unsubscribe(self.mqttSettings['mqtt_topic_control'])
				self.clientControl.disconnect()
			except:
				self.logger.exception("clientControl cleanup exception")
				print("clientControl cleanup exception")
				pass
		return

	###############################################################################
	# MQTT interaction functions

	def publish(self, data):
		"""Publish data to an MQTT topic

		@param data: The data to publish
		@return: None
		"""
		self.logger.debug("mqtt: pub '{}' to topic '{}'".format(data, self.mqttSettings['mqtt_topic_respond']))
		print("mqtt: pub '{}' to topic '{}'".format(data, self.mqttSettings['mqtt_topic_respond']))
		try:
			pahopub.single(
				topic=self.mqttSettings['mqtt_topic_respond'],
				payload=str(data),
				qos=1,
				retain=True,
				hostname=self.mqttSettings['mqtt_broker'],
				port=self.mqttSettings['mqtt_port'],
				client_id=self.mqttSettings['mqtt_client']
			)
		except Exception as e:
			self.logger.exception("mqtt: pub exception:\n{}".format(e))
			print("mqtt: pub exception:\n{}".format(e))
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

	def on_publish(self, client, userdata, mid, rc):
		"""Event handler for when the client attempts to publish to a topic

		@param client: the MQTT client that is publishing
		@param userdata: any special user data needed (currently unused but comes with automatically)
		@param mid: ??
		@param rc: results of publication
		@return:
		"""
		self.logger.debug("mqtt: (PUBLISH) mid: {}, rc: {}".format(mid, rc))
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
			print("taking picture now: {}".format(self.cameraFile))
			self.camera.capture(self.cameraFile)

			# tell the server where the file is for now... we'll figure out something else later
			self.publish(data=self.cameraFile)
		return
