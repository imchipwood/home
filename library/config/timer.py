from library.config import BaseConfiguration


class TimerKeys:
    FREQUENCY = "frequency"


class TimerConfig(BaseConfiguration):

    def __init__(self, config_path, mqtt_config=None, debug=False):
        super().__init__(config_path, debug)

        self.mqtt_config = mqtt_config
        if mqtt_config:
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def frequency(self) -> float:
        """
        Default frequency of 0.1Hz
        @rtype: float
        """
        return self.config.get(TimerKeys.FREQUENCY, 0.02)

    @property
    def period(self) -> float:
        return 1.0 / self.frequency

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to publish to for capture commands
        @return: topic(s) to publish to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_publish.values())
