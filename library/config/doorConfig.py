import json


class ConfigKeys:
	GPIO = "gpio"
	GPIO_PIN_CONTROL = "pin_control"
	GPIO_PIN_SENSOR = "pin_sensor"
	GPIO_RELAY_TOGGLE_DELAY = "relay_toggle_delay"
	MQTT = "mqtt"
	MQTT_CLIENT = "client"
	MQTT_BROKER = "broker"
	MQTT_PORT = "port"
	MQTT_TOPIC_CONTROL = "topic_control"
	MQTT_TOPIC_STATE = "topic_state"
	LOG_PATH = "log"


class MQTTSettings(object):
	def __init__(self, settingsDict):
		self._settings = settingsDict

	@property
	def client(self):
		return self._settings[ConfigKeys.MQTT_CLIENT]

	@property
	def broker(self):
		return self._settings[ConfigKeys.MQTT_BROKER]

	@property
	def port(self):
		return self._settings[ConfigKeys.MQTT_PORT]

	@property
	def topicControl(self):
		return self._settings[ConfigKeys.MQTT_TOPIC_CONTROL]

	@property
	def topicState(self):
		return self._settings[ConfigKeys.MQTT_TOPIC_STATE]

	def __iter__(self):
		for setting in self._settings.values():
			yield setting

	def __getitem__(self, item):
		return self._settings.get(item, None)

	def __repr__(self):
		return json.dumps(self._settings, indent=2)

	def items(self):
		return iter([(x, y) for x, y in self._settings.items()])

	def iteritems(self):
		return iter([(x, y) for x, y in self._settings.iteritems()])


class DoorConfig(object):

	def __init__(self, configPath, debug=False):
		"""
		@param configPath: path to config JSON file
		@type configPath: str
		@param debug: debug flag (Default: False)
		@type debug: bool
		"""
		super(DoorConfig, self).__init__()

		self.configPath = configPath
		self.debug = debug

		self._config = {}
		self.config = configPath

	@property
	def config(self):
		"""
		@rtype: dict[str, str]
		"""
		return self._config

	@config.setter
	def config(self, configPath):
		self._config = self._loadConfig(configPath)

	@property
	def mqtt(self):
		"""
		@rtype: MQTTSettings
		"""
		return MQTTSettings(self.config.get(ConfigKeys.MQTT, {}))

	@property
	def gpio(self):
		"""
		@rtype: dict[str, str]
		"""
		return self.config.get(ConfigKeys.GPIO, {})

	@property
	def log(self):
		"""
		@rtype: str
		"""
		return self.config.get(ConfigKeys.LOG_PATH)

	def _loadConfig(self, configPath):
		"""
		Load the configuration file into the dictionary
		@param configPath: path to config file
		@type configPath: str
		@rtype: dict
		"""
		with open(configPath, 'r') as inf:
			return json.load(inf)

	def __repr__(self):
		"""
		@rtype: str
		"""
		return json.dumps(self.config, indent=2)


if __name__ == "__main__":
	import os
	thisDir = os.path.dirname(__file__).replace("/library/sensors", "")
	confDir = os.path.join(thisDir, "config")

	confFile = os.path.join(confDir, "garageDoorController.json")

	config = DoorConfig(confFile)
	print(config)
	print(config.mqtt.broker)
	print(json.dumps(config.gpio, indent=2))
	print(config.log)
