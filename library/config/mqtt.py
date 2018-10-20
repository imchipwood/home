import json


class MQTTBaseConfig(object):

    def __init__(self, mqtt_config_path):
        """
        Base MQTT configuration handler with
        @param mqtt_config_path:
        @type mqtt_config_path:
        """
        super(MQTTBaseConfig, self).__init__()
        from library.config import ConfigKeys
        self.ConfigKeys = ConfigKeys
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
        from library.config import load_config
        self._config = load_config(config_path)

    @property
    def broker(self):
        """
        Get the MQTT broker URL
        @return: MQTT broker URL
        @rtype: str or None
        """
        return self.config.get(self.ConfigKeys.BROKER)

    @property
    def port(self):
        """
        Get the MQTT broker port
        @return: MQTT broker port
        @rtype: int or None
        """
        return self.config.get(self.ConfigKeys.PORT)

    def __repr__(self):
        return json.dumps(self.config, indent=2)


class MQTTConfig(MQTTBaseConfig):
    def __init__(self, mqtt_config_path, sensor_config_path):
        """
        Sensor-specific MQTT Configuration constructor
        @param mqtt_config_path: path to MQTT configuration JSON file
        @type mqtt_config_path: str
        @param sensor_config_path: path to sensor-specific configuration file
        @type sensor_config_path: str
        """
        super(MQTTConfig, self).__init__(mqtt_config_path)
        from library.config import load_config
        self.config.update(load_config(sensor_config_path).get(self.ConfigKeys.MQTT))

    @property
    def client_id(self):
        """
        Get the MQTT client ID
        @return: MQTT client ID
        @rtype: str
        """
        return self.config.get(self.ConfigKeys.CLIENT_ID, "")

    @client_id.setter
    def client_id(self, client_id):
        """
        Change the client ID
        @param client_id: new client ID
        @type client_id: str
        """
        self.config[self.ConfigKeys.CLIENT_ID] = client_id

    @property
    def topics_publish(self):
        """
        Get all topics to publish to
        @return: dict of publish topics
        @rtype: dict
        """
        return self.config.get(
            self.ConfigKeys.TOPICS, {}
        ).get(
            self.ConfigKeys.PUBLISH, {}
        )

    @property
    def topics_subscribe(self):
        """
        Get all topics to subscribe to
        @return: dict of subscribe topics
        @rtype: dict
        """
        return self.config.get(
            self.ConfigKeys.TOPICS, {}).get(
            self.ConfigKeys.SUBSCRIBE, {}
        )


if __name__ == "__main__":
    import os
    configpath = os.path.join(os.path.dirname(__file__), "..", "..", "config", "mqtt.json")
    sensorconfigpath = os.path.join(os.path.dirname(__file__), "..", "..", "config", "garage_door_monitor.json")

    config = MQTTConfig(configpath, sensorconfigpath)
    print(config)
    print(config.topics_publish.get('state'))
    print(config.client_id)

