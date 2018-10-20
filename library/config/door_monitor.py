from library.config import BaseConfiguration


class DoorMonitorConfig(BaseConfiguration):
	def __init__(self, config_path, mqttconfig=None):
		"""
		@param config_path: path to JSON configuration file
		@type config_path: str
		@param mqttconfig: MQTTConfig object if MQTT is to be used
		@type mqttconfig: library.config.mqttconfig.MQTTConfig
		"""
		super(DoorMonitorConfig, self).__init__(config_path)

		self.mqttconfig = mqttconfig

		# Update the base configuration for easy dumping later
		self.config.get('mqtt', {}).update(self.mqttconfig.config)

	@property
	def pin(self):
		"""
		Get the GPIO pin #
		@return: GPIO pin # for environment sensor
		@rtype: int
		"""
		return self.config.get('pin')

	@property
	def mqtttopic(self):
		"""
		Get the MQTT topic to publish state info to
		@return: topic to publish state info to
		@rtype: str
		"""
		return self.mqttconfig.topics_publish['state']
