import os

from library.config import BaseConfiguration

from library.config.mqttconfig import MQTTConfig
from library.config.environment import EnvironmentConfig
from library.config.door_monitor import DoorMonitorConfig

from library.controllers.environment import EnvironmentController


class ConfigurationHandler(BaseConfiguration):

	# TODO: Finalize these
	SENSOR_CLASS_MAP = {
		'environment': EnvironmentController,
		'door_monitor': None,
		'door_control': None
	}
	SENSOR_CONFIG_CLASS_MAP = {
		'environment': EnvironmentConfig,
		'door_monitor': DoorMonitorConfig,
		'door_control': None
	}

	def __init__(self, config_path):
		super(ConfigurationHandler, self).__init__(config_path)
		self._current_sensor = 0
		self.sensors = list(self.config.get('sensors', {}))

	# region Sensors

	@property
	def mqtt_config_path(self):
		"""
		Get the full path to the base MQTT configuration file
		@return: path to the base MQTT configuration file
		@rtype: str
		"""
		if os.path.exists(self.config.get('mqtt', '')):
			return self.config['mqtt']
		else:
			return self.normalize_config_path(self.config.get('mqtt'))

	def get_sensor_mqtt_config(self, sensor):
		"""
		Get the MQTT config class for the given sensor
		@param sensor: target sensor
		@type sensor: str
		@return: MQTT configuration object with sensor settings
		@rtype: MQTTConfig
		"""
		if sensor in self.sensor_paths:
			return MQTTConfig(self.mqtt_config_path, self.get_sensor_path(sensor))
		else:
			return None

	def get_sensor_config(self, sensor):
		"""
		Get the config class for the particular
		@param sensor: target sensor
		@type sensor: str
		@return: the sensor config object for the given sensor if supported
		@rtype: library.config.BaseConfiguration
		"""
		if sensor in self.SENSOR_CLASS_MAP and sensor in self.sensor_paths:
			return self.SENSOR_CONFIG_CLASS_MAP[sensor](
				self.sensor_paths[sensor],
				self.get_sensor_mqtt_config(sensor)
			)
		else:
			return None

	def get_sensor_controller(self, sensor):
		"""
		Get the sensor object for the given sensor
		@param sensor: target sensor
		@type sensor: str
		@return: sensor object
		@rtype: library.controllers.BaseController
		"""
		if sensor in self.SENSOR_CLASS_MAP:
			return self.SENSOR_CLASS_MAP[sensor](self.get_sensor_config(sensor))
		else:
			return None

	# endregion Sensors
	# region BuiltIns

	def __repr__(self):
		"""
		@rtype: str
		"""
		return "({})".format(", ".join(self.sensors))

	def __iter__(self):
		"""
		Yield a sensor one at a time
		@return: sensor controllers iteratively
		"""
		self._current_sensor = 0
		for sensor in self.config.get('sensors', {}):
			yield self.get_sensor_controller(sensor)

	def __next__(self):
		"""
		Get the next sensor
		@return: sensor controller
		"""
		if self._current_sensor < len(self.sensors):
			sensor = self.sensors[self._current_sensor]
			self._current_sensor += 1
			return self.get_sensor_controller(sensor)
		else:
			raise StopIteration

		# endregion BuiltIns


if __name__ == "__main__":
	configpath = "media.json"
	config = ConfigurationHandler(configpath)

	# mqttconfig = config.get_sensor_mqtt_config('environment')
	# print(mqttconfig.client_id)

	env = config.get_sensor_config('environment')
	# print(env)
	print(env.mqtt_config)
	print(env.pin)
	print(env.type)
