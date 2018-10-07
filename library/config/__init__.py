import os
import json

from definitions import CONFIG_DIR


class BaseConfiguration(object):
	def __init__(self, configpath):
		super(BaseConfiguration, self).__init__()

		self._configpath = ""
		self._config = {}
		self.config = configpath

	def __repr__(self):
		return json.dumps(self.config, indent=2)

	def loadconfig(self, configpath):
		"""
		Load a JSON config file and return its contents
		@param configpath: path to config file
		@type configpath: str
		@return: JSON data
		@rtype: dict
		"""
		with open(configpath, 'r') as inf:
			return json.load(inf)

	@property
	def config(self):
		"""
		Get the current config dict
		@return: current config dict
		@rtype: dict
		"""
		return self._config

	@config.setter
	def config(self, configpath):
		"""
		Set a new config using a path to a JSON file
		@param configpath: path to config file
		@type configpath: str
		"""
		configpath = self.normalizeconfigpath(configpath)
		self._configpath = configpath
		self._config = self.loadconfig(self._configpath)

	@staticmethod
	def normalizeconfigpath(configpath):
		"""
		Normalize a config file path to the config dir of the repo
		@param configpath: relative config path
		@type configpath: str
		@return: normalized, absolute config path
		@rtype: str or None
		"""
		if not configpath:
			return None
		elif os.path.exists(configpath):
			return configpath
		else:
			# Assume it's in the config directory
			return os.path.join(CONFIG_DIR, configpath)

	@property
	def sensorpaths(self):
		"""
		Get the sensor config path dict
		@return: dict of sensor config paths
		@rtype: dict[str, str]
		"""
		return self.config.get('sensors')

	def getsensorpath(self, sensor):
		"""
		Get the config path for the target sensor
		@param sensor: target sensor
		@type sensor: str
		@return: Path to sensor config
		@rtype: str
		"""
		return self.normalizeconfigpath(self.sensorpaths.get(sensor))

	@property
	def mqttpath(self):
		"""
		Get the path to the base MQTT configuration file
		@return: path to base MQTT configuration file if it exists
		@rtype: str or None
		"""
		return self.normalizeconfigpath(self.config.get('mqtt'))

	@property
	def log(self):
		return self.config.get('log')


class MQTTConfiguration(object):
	def __init__(self, mqttDict):
		super(MQTTConfiguration, self).__init__()

		self._config = {}
		self.config = mqttDict

	@property
	def config(self):
		"""
		Get the current config
		@return: configuration dict
		@rtype: dict[str, str]
		"""
		return self._config

	@config.setter
	def config(self, newConfig):
		"""
		Set a new config
		@param newConfig:
		@type newConfig:
		@return:
		@rtype:
		"""
		assert isinstance(newConfig, dict), "Configuration must be of type dict!"
		self._config = newConfig

		# Ensure there is a port - 1883 is the default used by MQTT servers
		self.config.setdefault('port', 1883)

	@property
	def client(self):
		"""
		Get the MQTT client name
		@rtype: str
		"""
		return self._config.get('client', "")

	@property
	def broker(self):
		"""
		Get the MQTT broker URL
		@rtype: str
		"""
		return self._config.get('broker', "")

	@property
	def port(self):
		"""
		Get the MQTT port
		@rtype: int or None
		"""
		if 'port' in self.config:
			return int(self._config.get('port'))
		else:
			return self.config.setdefault('port', 1883)

	def __iter__(self):
		for setting in self._config.values():
			yield setting

	def __getitem__(self, item):
		return self._config.get(item, None)

	def __repr__(self):
		return json.dumps(self._config, indent=2)

	def items(self):
		return iter([(x, y) for x, y in self._config.items()])

	def iteritems(self):
		return iter([(x, y) for x, y in self._config.iteritems()])
