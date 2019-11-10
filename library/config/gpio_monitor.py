"""
Basic single-GPIO monitoring configuration handler
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from library.config import BaseConfiguration
from library.data.database import Column

class CONFIG_KEYS:
    PIN = "gpio_pin"
    PULL_UP_DOWN = "gpio_pull_up_down"


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
            self.config.get(self.config_keys.MQTT, {}).update(self.mqtt_config.config)

    @property
    def pin(self) -> int:
        """
        Get the GPIO pin #
        @return: GPIO pin # for sensor
        @rtype: int
        """
        return self.config.get('gpio_pin')

    @property
    def pull_up_down(self) -> str:
        """
        Get GPIO pull up/down
        @return: whether or not GPIO is pull-up or pull-down
        @rtype: str
        """
        return self.config.get("gpio_pull_up_down")

    @property
    def mqtt_topic(self):
        """
        Get the MQTT topic(s) to publish state info to
        @return: topic(s) to publish state info to
        @rtype: list[library.config.mqtt.Topic]
        """
        return list(self.mqtt_config.topics_publish.values())

    @property
    def db_name(self):
        column_data = self.config.get("db")
        if not column_data:
            return ""
        return column_data.get("name")

    @property
    def db_columns(self):
        column_data = self.config.get("db")
        if not column_data:
            return []
        columns = []
        for column_dict in column_data.get("columns", []):
            column = Column(
                column_dict.get("col_name", ""),
                column_dict.get("col_type", ""),
                column_dict.get("col_key", ""),
            )
            columns.append(column)
        return columns
