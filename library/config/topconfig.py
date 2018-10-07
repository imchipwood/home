import json

from library.config import BaseConfiguration
from mqttconfig import MQTTConfig


class ConfigurationHandler(BaseConfiguration):
	def __init__(self, configpath):
		super(ConfigurationHandler, self).__init__(configpath)
		
		sensormqttconfigs = {}
		for sensor, path in self.sensorpaths.items():

	def getsensormqttconfig(self, sensorname):
		
