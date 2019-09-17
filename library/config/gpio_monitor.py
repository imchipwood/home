"""
Basic single-GPIO monitoring configuration handler
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from library.config import BaseConfiguration


class GPIOMonitorConfig(BaseConfiguration):
    """
    MQTT-enabled door monitoring configuration
    """
    def __init__(self, config_path, mqtt_config=None):
        """
        @param config_path: path to JSON configuration file
        @type config_path: str
        @param mqtt_config: MQTTConfig object if MQTT is to be used
        @type mqtt_config: library.config.mqtt.MQTTConfig
        """
        super(GPIOMonitorConfig, self).__init__(config_path)

        self.mqtt_config = mqtt_config

        # Update the base configuration for easy dumping later
        if mqtt_config:
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def pin(self):
        """
        Get the GPIO pin #
        @return: GPIO pin # for sensor
        @rtype: int
        """
        return self.config.get('pin')

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to publish state info to
        @return: topic(s) to publish state info to
        @rtype: list[library.config.mqtt.Topic]
        """
        if not self.mqtt_config.topics_publish:
            return None
        else:
            return list(self.mqtt_config.topics_publish.values())
