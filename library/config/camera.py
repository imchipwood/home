"""
Camera configuration
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from typing import List

import ephem

from library.config import BaseConfiguration, BaseConfigKeys


class ConfigKeys:
    SETTINGS = "settings"
    ISO = "iso"
    ISO_DAY = "day"
    ISO_NIGHT = "night"
    DELAY = BaseConfigKeys.DELAY
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

    def __init__(self, config_path, mqtt_config=None, debug=False):
        """
        @param config_path: path to JSON configuration file
        @type config_path: str
        @param mqtt_config: MQTTConfig object if MQTT is to be used
        @type mqtt_config: library.config.mqtt.MQTTConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config_path, debug)

        self.mqtt_config = mqtt_config

        # Update the base configuration for easy dumping later
        if mqtt_config:
            self.config.get(BaseConfigKeys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def settings(self) -> dict:
        """
        Get the camera settings dict
        @rtype: dict
        """
        return self.config.get(ConfigKeys.SETTINGS, {})

    @property
    def brightness(self) -> int:
        """
        @rtype: int
        """
        return self.settings.get(ConfigKeys.BRIGHTNESS)

    @property
    def contrast(self) -> int:
        """
        @rtype: int
        """
        return self.settings.get(ConfigKeys.CONTRAST)

    @property
    def delay(self) -> float:
        """
        @rtype: float
        """
        return self.settings.get(ConfigKeys.DELAY)

    @property
    def resolution(self) -> List[int]:
        """
        @rtype: list[int]
        """
        return self.settings.get(ConfigKeys.RESOLUTION)

    @property
    def rotation(self) -> int:
        """
        @rtype: int
        """
        return self.settings.get(ConfigKeys.ROTATION)

    @property
    def iso(self) -> int:
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
    def iso_day(self) -> int:
        """
        @rtype: int
        """
        return self.settings.get(
            ConfigKeys.ISO, {}
        ).get(
            ConfigKeys.ISO_DAY, 200
        )

    @property
    def iso_night(self) -> int:
        """
        @rtype: int
        """
        return self.settings.get(
            ConfigKeys.ISO, {}
        ).get(
            ConfigKeys.ISO_NIGHT, 800
        )

    @property
    def location(self) -> str:
        """
        @rtype: str
        """
        return self.settings.get(ConfigKeys.CITY)

    @property
    def capture_path(self) -> str:
        """
        @rtype: str
        """
        return self.config.get(ConfigKeys.CAPTURE_PATH)

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to subscribe to for capture commands
        @return: topic(s) to subscribe to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_subscribe.values())
