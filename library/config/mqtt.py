"""
MQTT JSON Configuration Handlers
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json


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
        @return: payload dictionary
        @rtype: dict
        """
        payload = self._info.get("payload", {})
        for key, val in payload.items():
            actual_val = kwargs.get(key)
            if type(val) != type(actual_val):
                if isinstance(val, str):
                    actual_val = val.format(actual_val)
                elif isinstance(val, float):
                    actual_val = float(actual_val)
                elif isinstance(val, int):
                    actual_val = int(actual_val)

            payload[key] = actual_val

        return json.dumps(payload)


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

