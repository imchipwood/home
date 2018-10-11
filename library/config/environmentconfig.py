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

	@property
	def units(self):
		"""
		Get the desired temperature units
		@return: temperature units
		@rtype: str
		"""
		return self.config.get('units')

	@property
	def mqtttopic(self):
		"""
		Get the MQTT topic to publish environment info to
		@return: topic to publish environment info to
		@rtype: str
		"""
		return self.mqttconfig.topics_publish['environment']

	@property
	def period(self):
		"""
		Get the period for reading the sensor
		@return: period in seconds. Default: 300
		@rtype: int
		"""
		return int(self.config.get('period', 5 * 60))
