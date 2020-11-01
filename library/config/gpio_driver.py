"""
Basic single-GPIO driver configuration handler
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging

from library import GPIODriverActiveDirection
from library.config import BaseConfiguration, BaseConfigKeys

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError, ModuleNotFoundError):  # pragma: no cover
    from library.sensors import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Failed to import RPi.GPIO - using mock library")
    from library.mock.mock_gpio import GPIO


class ConfigKeys:
    PIN = BaseConfigKeys.PIN
    TOGGLE_DELAY = "gpio_toggle_delay"
    ACTIVE_DIRECTION = "gpio_active_direction"


class GPIODriverConfig(BaseConfiguration):
    """
    MQTT-enabled GPIO driver configuration
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
    def pin(self) -> int:
        """
        Get the GPIO pin #
        @return: GPIO pin # for sensor
        @rtype: int
        """
        return self.config.get(ConfigKeys.PIN)

    @property
    def toggle_delay(self) -> float:
        """
        Get the toggle delay in seconds
        @return: how long to wait when toggling
        @rtype: float
        """
        return self.config.get(ConfigKeys.TOGGLE_DELAY)

    @property
    def active_direction(self) -> int:
        """
        Get whether or not GPIO is defined as active LOW or active HIGH
        @return: active LOW (GPIO.LOW) or active HIGH (GPIO.HIGH)
        @rtype: int
        """
        direction = self.config.get(ConfigKeys.ACTIVE_DIRECTION, GPIODriverActiveDirection.HIGH).upper()
        return GPIO.HIGH if direction == GPIODriverActiveDirection.HIGH else GPIO.LOW

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to subscribe to
        @return: topic(s) to subscribe to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_subscribe.values())
