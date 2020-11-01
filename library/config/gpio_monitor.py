"""
Basic single-GPIO monitoring configuration handler
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from library.config import BaseConfiguration, BaseConfigKeys


class ConfigKeys:
    PIN = BaseConfigKeys.PIN
    PULL_UP_DOWN = "gpio_pull_up_down"
    FREQUENCY = "gpio_monitor_frequency"


class GPIOMonitorConfig(BaseConfiguration):
    """
    MQTT-enabled door monitoring configuration
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
    def period(self) -> float:
        """
        Get the GPIO monitor period
        @rtype: float
        """
        return 1.0 / self.frequency

    @property
    def frequency(self) -> float:
        """
        Get the GPIO monitor frequency
        @rtype: float
        """
        return self.config.get(ConfigKeys.FREQUENCY, 1.0)

    @property
    def pin(self) -> int:
        """
        Get the GPIO pin #
        @return: GPIO pin # for sensor
        @rtype: int
        """
        return self.config.get(ConfigKeys.PIN)

    @property
    def pull_up_down(self) -> str:
        """
        Get GPIO pull up/down
        @return: whether or not GPIO is pull-up or pull-down
        @rtype: str
        """
        return self.config.get(ConfigKeys.PULL_UP_DOWN, "")

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to publish state info to
        @return: topic(s) to publish state info to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_publish.values())
