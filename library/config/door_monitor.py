from library.config import BaseConfiguration


class DoorMonitorConfig(BaseConfiguration):
	def __init__(self, config_path, mqtt_config=None):
		"""
		@param config_path: path to JSON configuration file
		@type config_path: str
		@param mqtt_config: MQTTConfig object if MQTT is to be used
		@type mqtt_config: library.config.mqtt.MQTTConfig
		"""
		super(DoorMonitorConfig, self).__init__(config_path)

		self.mqtt_config = mqtt_config

		# Update the base configuration for easy dumping later
		self.config.get('mqtt', {}).update(self.mqtt_config.config)

	@property
	def pin(self):
		"""
		Get the GPIO pin #
		@return: GPIO pin # for sensor
		@rtype: int
		"""
		return self.config.get('pin')

	@property
	def mqtt_topic(self):
		"""
		Get the MQTT topic to publish state info to
		@return: topic to publish state info to
		@rtype: str
		"""
		return self.mqtt_config.topics_publish['state']
