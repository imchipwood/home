"""
MQTT JSON Configuration Handlers
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
import re
import socket

from library.config import BaseConfiguration, BaseConfigKeys, PubSubKeys


def get_ip_address():
    """
    Get the machine's current IP address
    @rtype: str
    """
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    return host_ip


class Formatters:
    """
    Simple Formatting object for MQTT Topic payloads
    """

    def __init__(self):
        """
        Constructor for Formatters object
        """
        super()
        self._methods = [
            self._format_payload_string,
            self._format_payload_bool,
            self._format_payload_float,
            self._format_payload_int
        ]

    @staticmethod
    def _format_payload_string(expected_value, actual_value):
        """
        Convert payload actual value to string if that's expected
        @param expected_value: expected payload value type
        @param actual_value: payload value passed by sensor or controller
        @return: actual_value as formatted string or original actual_value if string not expected
        """
        if not isinstance(expected_value, str):
            return actual_value

        value = actual_value
        if "{" in expected_value:
            # value won't change if expected_value is not a string formatter
            new_value = expected_value.format(actual_value)
            if new_value != expected_value:
                value = new_value
        else:
            # Free-form string?
            valid_values = expected_value.split("|")
            if expected_value == "" or actual_value in valid_values:
                value = actual_value
            else:
                value = None

        return value

    @staticmethod
    def _format_payload_int(expected_value, actual_value):
        """
        Convert payload actual value to int if that's expected
        @param expected_value: expected payload value type
        @param actual_value: payload value passed by sensor or controller
        @return: actual_value as int or original actual_value if int not expected
        """
        if isinstance(expected_value, int):
            return int(actual_value)

        return actual_value

    @staticmethod
    def _format_payload_float(expected_value, actual_value):
        """
        Convert payload actual value to float if that's expected
        @param expected_value: expected payload value type
        @param actual_value: payload value passed by sensor or controller
        @return: actual_value as float or original actual_value if float not expected
        """
        if isinstance(expected_value, float):
            return float(actual_value)

        return actual_value

    @staticmethod
    def _format_payload_bool(expected_value, actual_value):
        """
        Convert payload actual value to bool if that's expected
        @param expected_value: expected payload value type
        @param actual_value: payload value passed by sensor or controller
        @return: actual_value as bool or original actual_value if bool not expected
        """
        if isinstance(expected_value, bool):
            return bool(actual_value)

        return actual_value

    def __iter__(self):
        """
        Iteratively return the formatting methods
        @rtype: method
        """
        for method in self._methods:
            yield method


class Topic:
    """
    Basic MQTT topic object with payload & pubsub properties
    """

    def __init__(self, name, info):
        """
        Topic constructor
        @param name: name of topic
        @type name: str
        @param info: config dict from config file
        @type info: dict
        """
        super()

        self.name = name
        self._info = info

    @property
    def pubsub(self) -> str:
        """
        Get the Topic's pub/sub type
        @return: pubsub string from config
        @rtype: str
        """
        return self._info.get(PubSubKeys.PUBSUB, "")

    @property
    def is_publish(self) -> bool:
        """
        Check if this topic is a publishing topic
        @rtype: bool
        """
        publish_keys = [PubSubKeys.PUBLISH, PubSubKeys.BOTH]
        return bool(
            re.search(
                self.pubsub,
                "|".join(publish_keys),
                re.I
            )
        )

    @property
    def raw_payload(self) -> dict:
        """
        Get the raw payload dict for this topic
        @rtype: dict
        """
        return self._info.get(PubSubKeys.PAYLOAD, {})

    def payload(self, **kwargs) -> str or dict:
        """
        Get the Topic's payload
        @return: payload as a string
        @rtype: str or dict
        """
        # Are we publishing or subscribing?
        if not self.is_publish:
            # Publishing - convert it to a string & let the controller figure out what to do with it
            return self.raw_payload

        # subscribing
        new_payload = {}

        # Convert all the values
        for expected_key, expected_val in self.raw_payload.items():
            # convert the value
            actual_val = kwargs.get(expected_key)
            actual_val = self.convert_payload_type(expected_val, actual_val)

            # Check we got the correct value
            if actual_val is None or actual_val == "":
                raise Exception(f"Missing payload key '{expected_key}'!")

            new_payload[expected_key] = actual_val

        # Convert the payload to a string
        return json.dumps(new_payload)

    @staticmethod
    def convert_payload_type(expected_value, actual_value):
        """
        Convert the value passed in to the payload creator to the
        type defined in the payload configuration
        @param expected_value: expected payload value type
        @param actual_value: payload value passed by sensor or controller
        @return: actual value converted to correct type
        """
        for formatter in Formatters():
            new_value = formatter(expected_value, actual_value)
            if new_value != actual_value:
                return new_value

        return actual_value

    def __repr__(self):
        """
        Represent topic as a string
        @rtype: str
        """
        return self.name


class MQTTBaseConfig(BaseConfiguration):
    """
    Base configuration object for MQTT communication - handles broker & port
    """

    def __init__(self, config_path, debug=False):
        """
        Base MQTT configuration handler with
        @param config_path: path to config file
        @type config_path: str
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config_path, debug)

    @property
    def broker(self) -> str:
        """
        Get the MQTT broker URL
        @return: MQTT broker URL
        @rtype: str
        """
        return self.config.get(BaseConfigKeys.BROKER, get_ip_address())

    @property
    def port(self) -> int:
        """
        Get the MQTT broker port
        @return: MQTT broker port
        @rtype: int
        """
        return self.config.get(BaseConfigKeys.PORT, 1883)


class MQTTConfig(MQTTBaseConfig):
    """
    Sensor-based MQTT config - adds client_id & pub/sub topic support
    """

    def __init__(self, config_path, sensor_config_path, debug=False):
        """
        Sensor-specific MQTT Configuration constructor
        @param config_path: path to MQTT configuration JSON file
        @type config_path: str
        @param sensor_config_path: path to sensor-specific configuration file
        @type sensor_config_path: str
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config_path, debug)
        sensor_config_path = self.normalize_config_path(sensor_config_path)
        self.config.update(self.load_config(sensor_config_path).get(BaseConfigKeys.MQTT))

    @property
    def client_id(self) -> str:
        """
        Get the MQTT client ID
        @return: MQTT client ID
        @rtype: str
        """
        return self.config.get(BaseConfigKeys.CLIENT_ID, "")

    @client_id.setter
    def client_id(self, client_id):
        """
        Change the client ID
        @param client_id: new client ID
        @type client_id: str
        """
        self.config[BaseConfigKeys.CLIENT_ID] = client_id

    @property
    def topics(self):
        """
        Get a dict of all topics
        @return: dictionary of all topics keyed by topic name
        @rtype: dict[str, Topic]
        """
        all_topics = self.config.get(BaseConfigKeys.TOPICS, {})
        topics = {}
        for topic, info in all_topics.items():
            topics[topic] = Topic(topic, info)
        return topics

    @property
    def topics_publish(self):
        """
        Get all topics to publish to
        @return: dict of publish topics
        @rtype: dict[str, Topic]
        """
        return {
            name: topic
            for name, topic in self.topics.items()
            if topic.pubsub in [PubSubKeys.PUBLISH, PubSubKeys.BOTH]
        }

    @property
    def topics_subscribe(self):
        """
        Get all topics to subscribe to
        @return: dict of subscribe topics
        @rtype: dict[str, Topic]
        """
        return {
            name: topic
            for name, topic in self.topics.items()
            if topic.pubsub in [PubSubKeys.SUBSCRIBE, PubSubKeys.BOTH]
        }

    @property
    def db_table_name(self) -> str or None:
        """
        Get the database table name to write data to
        @return: database table name for writing
        @rtype: str or None
        """
        # if no database table name is found, do not write data
        return self.config.get(BaseConfigKeys.TABLE_NAME)
