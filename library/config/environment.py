"""Environment
Environment sensor configuration
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from library.config import BaseConfiguration


class ConfigKeys:
    SENSOR_TYPE = "sensor_type"
    PIN = "pin"
    UNITS = "units"
    PERIOD = "period"


class EnvironmentConfig(BaseConfiguration):
    """
    Basic configuration for environment sensor
    Supports MQTT communication & the DHT11, DHT22, AM2302
    humidity/temperature sensors
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
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def sensor_type(self) -> int:
        """
        Get the sensor type
        @return: Adafruit_DHT type
        @rtype: int
        """
        return self.config.get(ConfigKeys.SENSOR_TYPE)

    @property
    def pin(self) -> int:
        """
        Get the GPIO pin #
        @return: GPIO pin # for environment sensor
        @rtype: int
        """
        return self.config.get(ConfigKeys.PIN)

    @property
    def units(self) -> str:
        """
        Get the desired temperature units
        @return: temperature units
        @rtype: str
        """
        return self.config.get(ConfigKeys.UNITS)

    @property
    def period(self) -> int:
        """
        Get the period for reading the sensor
        @return: period in seconds. Default: 300
        @rtype: int
        """
        return int(self.config.get(ConfigKeys.PERIOD, 5 * 60))

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to publish state info to
        @return: topic(s) to publish state info to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_publish.values())
