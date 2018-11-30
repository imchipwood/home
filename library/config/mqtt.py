"""
MQTT JSON Configuration Handlers
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json


class Formatters:
    """
    Simple Formatting object for MQTT Topic payloads
    """
    def __init__(self):
        """
        Constructor for Formatters object
        """
        super(Formatters, self).__init__()
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
        if isinstance(expected_value, str):
            # value won't change if expected_value is not a string formatter
            new_value = expected_value.format(actual_value)
            if new_value != expected_value:
                # Value changed - expected_value was a string formatter
                return new_value

        return actual_value

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


class Topic(object):
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
        super(Topic, self).__init__()

        self.name = name
        self._info = info

    @property
    def pubsub(self):
        """
        Get the Topic's pub/sub type
        @return: pubsub string from config
        @rtype: str
        """
        return self._info.get("pubsub", "").lower()

    def payload(self, **kwargs):
        """
        Get the Topic's payload
        @return: payload as a string
        @rtype: str
        """
        # Get the expected payload
        payload = self._info.get("payload", {})
        new_payload = {}

        # Convert all the values
        for expected_key, expected_val in payload.items():
            # convert the value
            actual_val = kwargs.get(expected_key)
            actual_val = self.convert_payload_type(expected_val, actual_val)

            # Check we got the correct value
            if actual_val is None or actual_val == "":
                raise Exception("Missing payload key '{}'!".format(expected_key))

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


class MQTTBaseConfig(object):
    """
    Base configuration object for MQTT communication - handles broker & port
    """
    def __init__(self, mqtt_config_path):
        """
        Base MQTT configuration handler with
        @param mqtt_config_path:
        @type mqtt_config_path:
        """
        super(MQTTBaseConfig, self).__init__()
        from library.config import ConfigKeys
        self.config_keys = ConfigKeys
        self._config = {}
        self.config = mqtt_config_path

    @property
    def config(self):
        """
        @rtype: dict
        """
        return self._config

    @config.setter
    def config(self, config_path):
        """
        Set a new config
        @param config_path: path to config file
        @type config_path: str
        """
        from library.config import load_config, normalize_config_path
        config_path = normalize_config_path(config_path)
        self._config = load_config(config_path)

    @property
    def broker(self):
        """
        Get the MQTT broker URL
        @return: MQTT broker URL
        @rtype: str or None
        """
        return self.config.get(self.config_keys.BROKER)

    @property
    def port(self):
        """
        Get the MQTT broker port
        @return: MQTT broker port
        @rtype: int or None
        """
        return self.config.get(self.config_keys.PORT)

    def __repr__(self):
        return json.dumps(self.config, indent=2)


class MQTTConfig(MQTTBaseConfig):
    """
    Sensor-based MQTT config - adds client_id & pub/sub topic support
    """
    def __init__(self, mqtt_config_path, sensor_config_path):
        """
        Sensor-specific MQTT Configuration constructor
        @param mqtt_config_path: path to MQTT configuration JSON file
        @type mqtt_config_path: str
        @param sensor_config_path: path to sensor-specific configuration file
        @type sensor_config_path: str
        """
        super(MQTTConfig, self).__init__(mqtt_config_path)
        from library.config import load_config, normalize_config_path
        sensor_config_path = normalize_config_path(sensor_config_path)
        self.config.update(load_config(sensor_config_path).get(self.config_keys.MQTT))

    @property
    def client_id(self):
        """
        Get the MQTT client ID
        @return: MQTT client ID
        @rtype: str
        """
        return self.config.get(self.config_keys.CLIENT_ID, "")

    @client_id.setter
    def client_id(self, client_id):
        """
        Change the client ID
        @param client_id: new client ID
        @type client_id: str
        """
        self.config[self.config_keys.CLIENT_ID] = client_id

    @property
    def topics(self):
        """
        Get a dict of all topics
        @return: dictionary of all topics keyed by topic name
        @rtype: dict[str, Topic]
        """
        all_topics = self.config.get(self.config_keys.TOPICS, {})
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
            if topic.pubsub in ["publish", "both"]
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
            if topic.pubsub in ["subscribe", "both"]
        }

