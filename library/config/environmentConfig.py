import json

from library.config import MQTTSettings


class ConfigKeys:
	SENSOR = "sensor"
	SENSOR_TYPE = "type"
	SENSOR_PIN = "pin"
	MQTT = "mqtt"
	MQTT_TOPIC_TEMPERATURE = "topic_temperature"
	MQTT_TOPIC_HUMIDITY = "topic_humidity"
	LOG_PATH = "log"


class EnvironmentMQTTSettings(MQTTSettings):
	def __init__(self, mqttDict):
		super(EnvironmentMQTTSettings, self).__init__(mqttDict)

	@property
	def topicTemperature(self):
		return self._config.get(ConfigKeys.MQTT_TOPIC_TEMPERATURE)

	@property
	def topicHumidity(self):
		return self._config.get(ConfigKeys.MQTT_TOPIC_HUMIDITY)


class EnvironmentConfig(object):
	def __init__(self, configPath, debug=False):
		super(EnvironmentConfig, self).__init__()

		self.configPath = configPath
		self.debug = debug

		self._config = {}

	@property
	def config(self):
		"""
		@rtype: dict[str, str]
		"""
		return self._config

	@config.setter
	def config(self, configPath):
		self._config = self._loadConfig(configPath)

	def _loadConfig(self, configPath):
		"""
		Load the configuration file into the dictionary
		@param configPath: path to config file
		@type configPath: str
		@rtype: dict
		"""
		with open(configPath, 'r') as inf:
			return json.load(inf)

	@property
	def log(self):
		"""
		@rtype: str
		"""
		return self.config.get(ConfigKeys.LOG_PATH)

	def __repr__(self):
		"""
		@rtype: str
		"""
		return json.dumps(self.config, indent=2)

	@property
	def mqtt(self):
		"""
		@rtype: DoorMQTTSettings
		"""
		return EnvironmentMQTTSettings(self.config.get(ConfigKeys.MQTT, {}))

	@property
	def dhtType(self):
		return self.config.get(ConfigKeys.SENSOR, {}).get(ConfigKeys.SENSOR_TYPE)

	@property
	def dhtPin(self):
		return self.config.get(ConfigKeys.SENSOR, {}).get(ConfigKeys.SENSOR_PIN)
