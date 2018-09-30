import json


class MQTTSettings(object):
	def __init__(self, mqttDict):
		super(MQTTSettings, self).__init__()

		self._config = mqttDict

	@property
	def client(self):
		return self._config.get('client')

	@property
	def broker(self):
		return self._config.get('broker')

	@property
	def port(self):
		return self._config.get('port')

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
