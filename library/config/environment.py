from library.config import BaseConfiguration


class EnvironmentConfig(BaseConfiguration):
	def __init__(self, config_path, mqtt_config=None):
		"""
		@param config_path: path to JSON configuration file
		@type config_path: str
		@param mqtt_config: MQTTConfig object if MQTT is to be used
		@type mqtt_config: library.config.mqttconfig.MQTTConfig
		"""
		super(EnvironmentConfig, self).__init__(config_path)

		self.mqtt_config = mqtt_config

		# Update the base configuration for easy dumping later
		self.config.get('mqtt', {}).update(self.mqtt_config.config)

	@property
	def type(self):
		"""
		Get the sensor type
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
	def mqtt_topic(self):
		"""
		Get the MQTT topic to publish state info to
		@return: topic to publish state info to
		@rtype: str
		"""
		return self.mqtt_config.topics_publish['environment']

	@property
	def period(self):
		"""
		Get the period for reading the sensor
		@return: period in seconds. Default: 300
		@rtype: int
		"""
		return int(self.config.get('period', 5 * 60))