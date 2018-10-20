import os
import json

from library import CONFIG_DIR


class BaseConfiguration(object):
	def __init__(self, config_path):
		super(BaseConfiguration, self).__init__()

		self._config_path = ""
		self._config = {}
		self.config = config_path

	def __repr__(self):
		return json.dumps(self.config, indent=2)

	def load_config(self, config_path):
		"""
		Load a JSON config file and return its contents
		@param config_path: path to config file
		@type config_path: str
		@return: JSON data
		@rtype: dict
		"""
		with open(config_path, 'r') as inf:
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
	def config(self, config_path):
		"""
		Set a new config using a path to a JSON file
		@param config_path: path to config file
		@type config_path: str
		"""
		config_path = self.normalize_config_path(config_path)
		self._config_path = config_path
		self._config = self.load_config(self._config_path)

	@staticmethod
	def normalize_config_path(config_path):
		"""
		Normalize a config file path to the config dir of the repo
		@param config_path: relative config path
		@type config_path: str
		@return: normalized, absolute config path
		@rtype: str or None
		"""
		if not config_path:
			return None
		elif os.path.exists(config_path):
			return config_path
		else:
			# Assume it's in the config directory
			return os.path.join(CONFIG_DIR, config_path)

	@property
	def sensor_paths(self):
		"""
		Get the sensor config path dict
		@return: dict of sensor config paths
		@rtype: dict[str, str]
		"""
		return self.config.get('sensors')

	def get_sensor_path(self, sensor):
		"""
		Get the config path for the target sensor
		@param sensor: target sensor
		@type sensor: str
		@return: Path to sensor config
		@rtype: str
		"""
		return self.normalize_config_path(self.sensor_paths.get(sensor))

	@property
	def mqtt_path(self):
		"""
		Get the path to the base MQTT configuration file
		@return: path to base MQTT configuration file if it exists
		@rtype: str or None
		"""
		return self.normalize_config_path(self.config.get('mqtt'))

	@property
	def log(self):
		return self.config.get('log')


class MQTTConfiguration(object):
	def __init__(self, mqtt_dict):
		super(MQTTConfiguration, self).__init__()

		self._config = {}
		self.config = mqtt_dict

	@property
	def config(self):
		"""
		Get the current config
		@return: configuration dict
		@rtype: dict[str, str]
		"""
		return self._config

	@config.setter
	def config(self, config):
		"""
		Set a new config
		@param config:
		@type config:
		@return:
		@rtype:
		"""
		assert isinstance(config, dict), "Configuration must be of type dict!"
		self._config = config

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
