"""
MQTT Environment Configuration
Author: github.com/imchipwood
"""
from typing import List

from library.config import BaseConfiguration, BaseConfigKeys


class MqttEnvironmentConfig(BaseConfiguration):
    """
    Configuration of MQTT Environment sensor reading
    Houses configuration of MQTT topics
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
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to subscribe to for environment data
        @return: topic(s) to subscribe to
        @rtype: List[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_subscribe.values())