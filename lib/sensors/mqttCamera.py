
import logging
from time import sleep
import paho.mqtt.client as paho
import paho.mqtt.publish as pahopub
from picamera import PiCamera
from multiprocessing import Process


class MQTTError(BaseException):
	pass


class MqttCamera(object):
	def __init__(self, configFile, debug=False):
		# super(MqttCamera, self).__init__()
		print("mqttCamera init")
		# set up logging first
		loggingLevel = logging.INFO
		if debug:
			loggingLevel = logging.DEBUG
		self.logger = logging.getLogger(__name__)

		# formatting - add this to logging handler
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)

		# stdout handler
		ch = logging.StreamHandler()
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
		self.camera = self.setupCamera(cameraSettings)

		self.clientControl = None
		self.controlThread = Process(target=self.control, args=[])
		return
	
	def setupCamera(self, cameraSettingsDict):
		camera = PiCamera()
		camera.rotation = cameraSettingsDict['camera_rotation']
		camera.brightness = cameraSettingsDict['camera_brightness']
		camera.contrast = cameraSettingsDict['camera_contrast']
		self.cameraFile = cameraSettingsDict['camera_filepath']
		camera.start_preview()
		return camera

	def parseConfig(self, cfgFile):
		cameraSettings = {}
		mqttSettings = {}

		with open(cfgFile, 'r') as inf:
			lines = inf.readlines()
		logFile = None
		for line in lines:
			line = line.rstrip().split("=")
			key, val = line[:2]
			try:
				val = int(val)
			except:
				pass
			if 'camera' in key:
				cameraSettings[key] = val
			elif 'mqtt' in key:
				mqttSettings[key] = val
			elif key == 'log':
				logFile = val

		s = 'Camera settings:\n'
		for key, val in cameraSettings.items():
			s += "{}: {}\n".format(key, val)
		logging.debug(s)
		s = 'MQTT settings:\n'
		for key, val in mqttSettings.items():
			s += "{}: {}\n".format(key, val)
		logging.debug(s)
		return cameraSettings, mqttSettings, logFile

	def cleanup(self):
		try:
			self.camera.stop_preview()
		except:
			pass
		return

	def start(self):
		# launch control thread
		try:
			self.logger.debug("start control thread")
			self.controlThread.start()
		except:
			self.logger.exception("failed to start control thread")
			self.cleanup()
			raise
		return

	def control(self):
		self.clientControl = paho.Client(client_id=self.mqttSettings['mqtt_client'])
		self.clientControl.on_connect = self.on_connect
		self.clientControl.on_subscribe = self.on_subscribe
		self.clientControl.on_message = self.on_message
		self.clientControl.connect(self.mqttSettings['mqtt_broker'], self.mqttSettings['mqtt_port'])
		# begin control loop
		try:
			self.logger.debug("control loop_forever")
			self.clientControl.loop_forever()  # blocking
		except:
			# clean up in case of emergency
			try:
				self.logger.debug("clientControl cleaning up")
				self.clientControl.loop_stop()
				self.clientControl.unsubscribe(self.mqttSettings['mqtt_topic_control'])
				self.clientControl.disconnect()
			except:
				self.logger.exception("clientControl cleanup exception")
				pass
		return

	###############################################################################
	# MQTT interaction functions

	def publish(self, data):
		self.logger.debug("mqtt: pub '{}' to topic '{}'".format(data, self.mqttSettings['mqtt_topic_respond']))
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
			pass
		return

	def on_connect(self, client, userdata, flags, rc):
		self.logger.debug("mqtt: (CONNECTION) received with code {}".format(rc))
		client.subscribe(self.mqttSettings['mqtt_topic_control'], qos=1)
		# MQTTCLIENT_SUCCESS = 0, all others are some kind of error.
		# attempt to reconnect on errors
		if rc != 0:
			if rc == -4:
				self.logger.exception("mqtt: ERROR: 'too many messages'\n")
			elif rc == -5:
				self.logger.exception("mqtt: ERROR: 'invalid UTF-8 string'\n")
			elif rc == -9:
				self.logger.exception("mqtt: ERROR: 'bad QoS'\n")
			raise MQTTError("on_connect 'rc' failure")
		return

	def on_subscribe(self, client, userdata, mid, granted_qos):
		self.logger.debug("mqtt: (SUBSCRIBE) mid: {}, granted_qos: {}".format(mid, granted_qos))
		return

	def on_publish(self, client, userdata, mid, rc):
		self.logger.debug("mqtt: (PUBLISH) mid: {}".format(mid))
		return

	def on_message(self, client, userdata, msg):
		self.logger.debug("mqtt: (RX) topic: {}, QOS: {}, payload: {}".format(msg.topic, msg.qos, msg.payload))
		if msg.topic == self.mqttSettings['mqtt_topic_control'] and msg.payload == 'CAPTURE':
			self.camera.capture(self.cameraFile)

		# tell the server where the file is for now... we'll figure out something else later
		self.publish(data=self.cameraFile)
		return
