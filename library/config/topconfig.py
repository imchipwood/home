import os

from library.config import BaseConfiguration

from library.config.mqttconfig import MQTTConfig
from library.config.environmentconfig import EnvironmentConfig

from library.controllers.environmentcontroller import EnvironmentController


class ConfigurationHandler(BaseConfiguration):

	# TODO: Finalize these
	SENSOR_CLASS_MAP = {
		'environment': EnvironmentController,
		'door_monitor': None,
		'door_control': None
	}
	SENSOR_CONFIG_CLASS_MAP = {
		'environment': EnvironmentConfig,
		'door_monitor': None,
		'door_control': None
	}

	def __init__(self, configpath):
		super(ConfigurationHandler, self).__init__(configpath)

	@property
	def mqttconfigpath(self):
		"""
		Get the full path to the base MQTT configuration file
		@return: path to the base MQTT configuration file
		@rtype: str
		"""
		if os.path.exists(self.config.get('mqtt', '')):
			return self.config['mqtt']
		else:
			return self.normalizeconfigpath(self.config.get('mqtt'))

	def getsensormqttconfig(self, sensor):
		"""
		Get the MQTT config class for the given sensor
		@param sensor: target sensor
		@type sensor: str
		@return: MQTT configuration object with sensor settings
		@rtype: MQTTConfig
		"""
		if sensor in self.sensorpaths:
			return MQTTConfig(self.mqttconfigpath, self.getsensorpath(sensor))
		else:
			return None

	def getsensorconfig(self, sensor):
		"""
		Get the config class for the particular
		@param sensor: target sensor
		@type sensor: str
		@return: the sensor config object for the given sensor if supported
		@rtype: object or None
		"""
		if sensor in self.SENSOR_CLASS_MAP and sensor in self.sensorpaths:
			return self.SENSOR_CONFIG_CLASS_MAP[sensor](
				self.sensorpaths[sensor],
				self.getsensormqttconfig(sensor)
			)
		else:
			return None

	def getsensorcontroller(self, sensor):
		"""
		Get the sensor object for the given sensor
		@param sensor: target sensor
		@type sensor: str
		@return: sensor object
		@rtype: object
		"""
		if sensor in self.SENSOR_CLASS_MAP:
			return self.SENSOR_CLASS_MAP[sensor](self.getsensorconfig(sensor))
		else:
			return None


if __name__ == "__main__":
	configpath = "media.json"
	config = ConfigurationHandler(configpath)

	# mqttconfig = config.getsensormqttconfig('environment')
	# print(mqttconfig.client_id)

	env = config.getsensorconfig('environment')
	# print(env)
	print(env.mqttconfig)
	print(env.pin)
	print(env.type)
