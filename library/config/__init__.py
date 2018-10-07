import json


class BaseConfiguration(object):
	def __init__(self, configpath):
		super(BaseConfiguration, self).__init__()

		self._config = {}
		self.config = configpath

	def loadconfig(self, configpath):
		with open(configpath, 'r') as inf:
			return json.load(inf)

	@property
	def config(self):
		return self._config

	@config.setter
	def config(self, configpath):
		self._config = self.loadconfig(configpath)

	@property
	def sensorpaths(self):
		return self.config.get('sensors')

	@property
	def mqttpath(self):
		return self.config.get('mqtt')


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
