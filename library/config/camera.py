"""
Camera configuration
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""

from library.config import BaseConfiguration
import ephem


class CameraConfigKeys:
    SETTINGS = "settings"
    ISO = "iso"
    ISO_DAY = "day"
    ISO_NIGHT = "night"
    DELAY = "delay"
    RESOLUTION = "resolution"
    ROTATION = "rotation"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    CITY = "city"
    CAPTURE_PATH = "capture_path"


class CameraConfig(BaseConfiguration):
    """
    Configuration of Pi Camera
    Image support only
    Supports MQTT communication to start a capture
    """
    def __init__(self, config_path, mqtt_config=None):
        """
        @param config_path: path to JSON configuration file
        @type config_path: str
        @param mqtt_config: MQTTConfig object if MQTT is to be used
        @type mqtt_config: library.config.mqtt.MQTTConfig
        """
        super(CameraConfig, self).__init__(config_path)

        self.mqtt_config = mqtt_config

        # Update the base configuration for easy dumping later
        self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def settings(self):
        """
        Get the camera settings dict
        @rtype: dict
        """
        return self.config.get('settings', {})

    @property
    def brightness(self):
        """
        @rtype: int
        """
        return self.settings.get(CameraConfigKeys.BRIGHTNESS)

    @property
    def contrast(self):
        """
        @rtype: int
        """
        return self.settings.get(CameraConfigKeys.CONTRAST)

    @property
    def delay(self):
        """
        @rtype: float
        """
        return self.settings.get(CameraConfigKeys.DELAY)

    @property
    def resolution(self):
        """
        @rtype: list[int]
        """
        return self.settings.get(CameraConfigKeys.RESOLUTION)

    @property
    def rotation(self):
        """
        @rtype: int
        """
        return self.settings.get(CameraConfigKeys.ROTATION)

    @property
    def iso(self):
        """
        Calculate the iso based on the time of day
        @rtype: int
        """
        sun = ephem.Sun()
        city = ephem.city(self.location)
        sun.compute(city)
        # twilight = -12 * ephem.degree
        # daytime = sun.alt < twilight
        daytime = sun.alt > 0

        if daytime:
            return self.iso_day
        else:
            return self.iso_night

    @property
    def iso_day(self):
        """
        @rtype: int
        """
        return self.settings.get(
            CameraConfigKeys.ISO, {}
        ).get(
            CameraConfigKeys.ISO_DAY, 200
        )

    @property
    def iso_night(self):
        """
        @rtype: int
        """
        return self.settings.get(
            CameraConfigKeys.ISO, {}
        ).get(
            CameraConfigKeys.ISO_NIGHT, 800
        )

    @property
    def location(self):
        """
        @rtype: int
        """
        return self.settings.get(CameraConfigKeys.CITY)

    @property
    def capture_path(self):
        """
        @rtype: str
        """
        return self.config.get(CameraConfigKeys.CAPTURE_PATH)

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to subscribe to for capture commands
        @return: topic(s) to subscribe to
        @rtype: list[library.config.mqtt.Topic]
        """
        if not self.mqtt_config.topics_subscribe:
            return None
        else:
            return list(self.mqtt_config.topics_subscribe.values())