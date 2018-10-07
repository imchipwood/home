from library.config import BaseConfiguration


class EnvironmentConfig(BaseConfiguration):
	def __init__(self, configpath, mqttconfig=None):
		"""
		@param configpath: path to JSON configuration file
		@type configpath: str
		@param mqttconfig: MQTTConfig object if MQTT is to be used
		@type mqttconfig: library.config.mqttconfig.MQTTConfig
		"""
		super(EnvironmentConfig, self).__init__(configpath)

		self.mqttconfig = mqttconfig

		# Update the base configuration for easy dumping later
		self.config.get('mqtt', {}).update(self.mqttconfig.config)

	@property
	def type(self):
		"""
		Get the environment sensor type
		@return: Adafruit_DHT type
		@rtype: int
		"""
		return self.config.get('type')

	@property
	def pin(self):
		"""
		Get the GPIO pin #
		@return: GPIO pin # for environment sensor
		@rtype: int
		"""
		return self.config.get('pin')
