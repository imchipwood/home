import json


class CameraConfig(object):
	class ConfigKeys:
		SETTINGS = "settings"
		SETTINGS_ISO = "iso"
		SETTINGS_ISO_DAY = "day"
		SETTINGS_ISO_NIGHT = "night"
		SETTINGS_DELAY = "delay"
		SETTINGS_RESOLUTION = "resolution"
		SETTINGS_ROTATION = "rotation"
		SETTINGS_BRIGHTNESS = "brightness"
		SETTINGS_CONTRAST = "contrast"
		LOCATION = "location"
		LOCATION_CITY = "city"
		CAPTURE_PATH = "capture_path"
		LOG = "log"

	def __init__(self, configPath, debug=False):
		"""
		@param configPath: path to config JSON file
		@type configPath: str
		@param debug: debug flag (Default: False)
		@type debug: bool
		"""
		super(CameraConfig, self).__init__()

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
	def settings(self):
		"""
		@rtype: dict[str, str]
		"""
		return self.config.get(self.ConfigKeys.SETTINGS, {})

	@property
	def log(self):
		"""
		@rtype: str
		"""
		return self.config.get(self.ConfigKeys.LOG_PATH)

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
	thisDir = os.path.dirname(__file__).replace("/lib/sensors", "")
	confDir = os.path.join(thisDir, "conf")

	confFile = os.path.join(confDir, "garageDoorCamera.json")

	config = CameraConfig(confFile)
	print(config)
	print(json.dumps(config.mqtt, indent=2))
	print(json.dumps(config.gpio, indent=2))
	print(config.log)
