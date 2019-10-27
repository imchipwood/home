"""Environment
Environment sensor configuration
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""

from library.config import BaseConfiguration


class EnvironmentConfig(BaseConfiguration):
    """
    Basic configuration for environment sensor
    Supports MQTT communication & the DHT11, DHT22, AM2302
    humidity/temperature sensors
    """
    def __init__(self, config_path, mqtt_config=None):
        """
        @param config_path: path to JSON configuration file
        @type config_path: str
        @param mqtt_config: MQTTConfig object if MQTT is to be used
        @type mqtt_config: library.config.mqtt.MQTTConfig
        """
        super().__init__(config_path)

        self.mqtt_config = mqtt_config

        # Update the base configuration for easy dumping later
        if mqtt_config:
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def type(self) -> int:
        """
        Get the sensor type
        @return: Adafruit_DHT type
        @rtype: int
        """
        return self.config.get('type')

    @property
    def pin(self) -> int:
        """
        Get the GPIO pin #
        @return: GPIO pin # for environment sensor
        @rtype: int
        """
        return self.config.get('pin')

    @property
    def units(self) -> str:
        """
        Get the desired temperature units
        @return: temperature units
        @rtype: str
        """
        return self.config.get('units')

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic to publish state info to
        @return: topic to publish state info to
        @rtype: library.config.mqtt.Topic
        """
        if not self.mqtt_config.topics_publish:
            return None
        elif len(self.mqtt_config.topics_publish) == 1:
            return list(self.mqtt_config.topics_publish.values())[0]
        else:
            raise Exception("Multiple publish topics defined")

    @property
    def period(self) -> int:
        """
        Get the period for reading the sensor
        @return: period in seconds. Default: 300
        @rtype: int
        """
        return int(self.config.get('period', 5 * 60))
