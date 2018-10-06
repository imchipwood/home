import json


class MQTTBaseConfig(object):
	def __init__(self, mqttconfigpath):
		super(MQTTBaseConfig, self).__init__()
		self._config = {}
		self.config = mqttconfigpath

	def loadconfig(self, configpath):
		"""
		Parse a config file
		@param configpath: path to config file
		@type configpath: str
		@return: data from config file
		@rtype: dict
		"""
		with open(configpath, 'r') as inf:
			return json.load(inf)

	@property
	def config(self):
		"""
		@rtype: dict
		"""
		return self._config

	@config.setter
	def config(self, configpath):
		"""
		Set a new config
		@param configpath: path to config file
		@type configpath: str
		"""
		self._config = self.loadconfig(configpath)

	@property
	def broker(self):
		"""
		Get the MQTT broker URL
		@return: MQTT broker URL
		@rtype: str or None
		"""
		return self.config.get('broker')

	@property
	def port(self):
		"""
		Get the MQTT broker port
		@return: MQTT broker port
		@rtype: int or None
		"""
		return self.config.get('port')

	def __repr__(self):
		return json.dumps(self.config, indent=2)


class MQTTConfig(MQTTBaseConfig):
	def __init__(self, mqttconfigpath, sensorconfigpath):
		super(MQTTConfig, self).__init__(mqttconfigpath)
		self.config.update(self.loadconfig(sensorconfigpath).get('mqtt'))

	@property
	def client_id(self):
		"""
		Get the MQTT client ID
		@return: MQTT client ID
		@rtype: str
		"""
		return self.config.get('client_id', "")

	@property
	def topics_publish(self):
		"""
		Get all topics to publish to
		@return: dict of publish topics
		@rtype: dict
		"""
		return self.config.get('topics', {}).get('publish', {})

	@property
	def topics_subscribe(self):
		"""
		Get all topics to subscribe to
		@return: dict of subscribe topics
		@rtype: dict
		"""
		return self.config.get('topics', {}).get('subscribe', {})

	def __repr__(self):
		return self.client_id or ""


if __name__ == "__main__":
	import os
	configpath = os.path.join(os.path.dirname(__file__), "..", "..", "config", "mqtt.json")
	sensorconfigpath = os.path.join(os.path.dirname(__file__), "..", "..", "config", "garage_door_monitor.json")

	config = MQTTConfig(configpath, sensorconfigpath)
	print(config)
	print(config.topics_publish.get('state'))

