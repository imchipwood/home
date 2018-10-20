import json


class MQTTBaseConfig(object):
	def __init__(self, mqtt_config_path):
		super(MQTTBaseConfig, self).__init__()
		self._config = {}
		self.config = mqtt_config_path

	def load_config(self, config_path):
		"""
		Parse a config file
		@param config_path: path to config file
		@type config_path: str
		@return: data from config file
		@rtype: dict
		"""
		with open(config_path, 'r') as inf:
			return json.load(inf)

	@property
	def config(self):
		"""
		@rtype: dict
		"""
		return self._config

	@config.setter
	def config(self, config_path):
		"""
		Set a new config
		@param config_path: path to config file
		@type config_path: str
		"""
		self._config = self.load_config(config_path)

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
	def __init__(self, mqtt_config_path, sensor_config_path):
		super(MQTTConfig, self).__init__(mqtt_config_path)
		self.config.update(self.load_config(sensor_config_path).get('mqtt'))

	@property
	def client_id(self):
		"""
		Get the MQTT client ID
		@return: MQTT client ID
		@rtype: str
		"""
		return self.config.get('client_id', "")

	@client_id.setter
	def client_id(self, client_id):
		"""
		Change the client ID
		@param client_id: new client ID
		@type client_id: str
		"""
		self.config['client_id'] = client_id

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


if __name__ == "__main__":
	import os
	configpath = os.path.join(os.path.dirname(__file__), "..", "..", "config", "mqtt.json")
	sensorconfigpath = os.path.join(os.path.dirname(__file__), "..", "..", "config", "garage_door_monitor.json")

	config = MQTTConfig(configpath, sensorconfigpath)
	print(config)
	print(config.topics_publish.get('state'))
	print(config.client_id)

