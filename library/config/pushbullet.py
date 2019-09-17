"""Pushbullet
Pushbullet "Sensor" Configuration
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from library.config import BaseConfiguration


class PushbulletConfig(BaseConfiguration):
    def __init__(self, config_path, mqtt_config=None):
        """
        @param config_path:
        @type config_path:
        @param mqtt_config: MQTTConfig object if MQTT is to be used
        @type mqtt_config: library.config.mqtt.MQTTConfig
        """
        super(PushbulletConfig, self).__init__(config_path)

        self.mqtt_config = mqtt_config

        # Update the base configuration for easy dumping later
        if mqtt_config:
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def api_key(self):
        """
        @rtype: str
        """
        return self.config.get("api")

    @property
    def notify(self):
        """
        @rtype: dict
        """
        return self.config.get("notify")

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to subscribe to for publishing
        @return: topic(s) to subscribe to
        @rtype: list[library.config.mqtt.Topic]
        """
        if not self.mqtt_config.topics_subscribe:
            return None
        else:
            return list(self.mqtt_config.topics_subscribe.values())
