import json

from library.config import MQTTConfiguration


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


class DoorMQTTConfiguration(MQTTConfiguration):
	def __init__(self, mqttDict):
		super(DoorMQTTConfiguration, self).__init__(mqttDict)

	@property
	def topicControl(self):
		"""
		Get the control topic name
		@rtype: str
		"""
		return self._config.get(ConfigKeys.MQTT_TOPIC_CONTROL, "")

	@property
	def topicState(self):
		"""
		Get the state topic name
		@rtype: str
		"""
		return self._config.get(ConfigKeys.MQTT_TOPIC_STATE, "")


class DoorGPIOConfiguration(object):
	def __init__(self, gpioDict):
		super(DoorGPIOConfiguration, self).__init__()

		self._config = {}
		self.config = gpioDict

	def __repr__(self):
		return json.dumps(self.config, indent=2)

	@property
	def config(self):
		return self._config

	@config.setter
	def config(self, gpioDict):
		assert isinstance(gpioDict, dict), "Configuration must be of type dict"
		self._config = gpioDict
		self.config.setdefault('relay_toggle_delay', 0.3)

	@property
	def pinControl(self):
		"""
		Get the control pin GPIO #
		@return: control pin GPIO #
		@rtype: int or None
		"""
		if 'pin_control' in self.config:
			return int(self.config.get('pin_control'))
		else:
			return None

	@property
	def pinSensor(self):
		"""
		Get the sense pin GPIO #
		@return: sense pin GPIO #
		@rtype: int or None
		"""
		if 'pin_sensor' in self.config:
			return int(self.config.get('pin_sensor'))
		else:
			return None

	@property
	def relayToggleDelay(self):
		"""
		Get the relay toggle delay duration
		@return: relay toggle delay duration
		@rtype: float or None
		"""
		if 'relay_toggle_delay' in self.config:
			return float(self.config.get('relay_toggle_delay'))
		else:
			return None


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
		@rtype: DoorMQTTConfiguration
		"""
		return DoorMQTTConfiguration(self.config.get(ConfigKeys.MQTT, {}))

	@property
	def gpio(self):
		"""
		@rtype: DoorGPIOConfiguration
		"""
		return DoorGPIOConfiguration(self.config.get(ConfigKeys.GPIO, {}))

	@property
	def log(self):
		"""
		@rtype: str or None
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
