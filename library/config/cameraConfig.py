import json
import ephem


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
        LOG_PATH = "log"

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
    def brightness(self):
        """
        @rtype: int
        """
        return self.settings.get(self.ConfigKeys.SETTINGS_BRIGHTNESS, 50)

    @property
    def contrast(self):
        """
        @rtype: int
        """
        return self.settings.get(self.ConfigKeys.SETTINGS_CONTRAST, 0)

    @property
    def rotation(self):
        """
        @rtype: int
        """
        return self.settings.get(self.ConfigKeys.SETTINGS_ROTATION, 180)

    @property
    def resolution(self):
        """
        @rtype: list[int]
        """
        return self.settings.get(self.ConfigKeys.SETTINGS_RESOLUTION, [3280, 2464])

    @property
    def captureDelay(self):
        """
        @rtype: float
        """
        return self.settings.get(self.ConfigKeys.SETTINGS_DELAY, 10.0)

    @property
    def iso(self):
        """
        Calculate the ISO based on whether or not it's nighttime
        @rtype: int
        """
        sun = ephem.Sun()
        city = self.config.get(self.ConfigKeys.LOCATION, {}).get(self.ConfigKeys.LOCATION_CITY, "Seattle")
        sea = ephem.city(city)
        sun.compute(sea)
        # twilight = -12 * ephem.degree
        # daytime = sun.alt < twilight
        daytime = sun.alt > 0

        daytimeISO = self.settings.get(self.ConfigKeys.SETTINGS_ISO, {}).get(self.ConfigKeys.SETTINGS_ISO_DAY, 200)
        nighttimeISO = self.settings.get(self.ConfigKeys.SETTINGS_ISO, {}).get(self.ConfigKeys.SETTINGS_ISO_NIGHT, 800)

        iso = daytimeISO
        if not daytime:
            iso = nighttimeISO

        return iso

    @property
    def capturePath(self):
        """
        @rtype: str
        """
        return self.config.get(self.ConfigKeys.CAPTURE_PATH, "")

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
    thisDir = os.path.dirname(__file__).replace("/library/sensors", "")
    confDir = os.path.join(thisDir, "config")

    confFile = os.path.join(confDir, "garageDoorCamera.json")

    config = CameraConfig(confFile)
    print(config)
    print(config.iso)
    print(config.brightness)
    print(config.contrast)
    print(config.captureDelay)
    print(config.capturePath)
    # print(json.dumps(config.mqtt, indent=2))
    # print(json.dumps(config.gpio, indent=2))
    print(config.log)
