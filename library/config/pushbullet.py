"""Pushbullet
Pushbullet "Sensor" Configuration
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from library.config import BaseConfiguration


class PushbulletConfig(BaseConfiguration):
    def __init__(self, config_path, mqtt_config=None, debug=False):
        """
        @param config_path: config file path
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
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def api_key(self) -> str:
        """
        @rtype: str
        """
        return self.config.get("api")

    @property
    def notify(self) -> dict:
        """
        @rtype: dict
        """
        return self.config.get("notify")

    @property
    def max_notification_delay(self) -> float:
        """
        @rtype: float
        """
        return self.config.get("max_notification_delay", 15.0)

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to subscribe to for publishing
        @return: topic(s) to subscribe to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_subscribe.values())
