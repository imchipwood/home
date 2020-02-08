"""
Basic MQTT Client with MQTTConfig constructor support
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
from paho.mqtt.client import Client, MQTTv311
from paho.mqtt import publish


class MQTTError(Exception):
    pass


def Get_MQTT_Error_Message(rc):
    """
    Get a human-readable error message from an MQTT return code
    @param rc: return code
    @type rc: int
    @return: Human-readable error message
    @rtype: str
    """
    if rc == 0:
        return ""
    # Something bad happened
    message = f"Error: rc={rc}, "
    if rc == -4:
        message += "Too many messages"
    elif rc == -5:
        message += "Invalid UTF-8 string"
    elif rc == -9:
        message += "Bad QoS"
    return message


class MQTTClient(Client):
    """
    paho.mqtt.client with support for passing in MQTTConfig object
    for initialization instead of manually defining client_id, etc.
    """
    def __init__(self, client_id="", clean_session=True, userdata=None, protocol=MQTTv311, transport="tcp", mqtt_config=None):
        """
        @type mqtt_config: library.config.mqtt.MQTTConfig
        """
        self.config = mqtt_config
        super().__init__(
            client_id=self.config.client_id if mqtt_config else client_id,
            clean_session=clean_session,
            userdata=userdata,
            protocol=protocol,
            transport=transport
        )

    def connect(self, host="", port=None, keepalive=60, bind_address=""):
        """
        Override connect with info from config if args are not provided
        @param host: hostname or IP address of the remote broker.
        @type host: str or None
        @param port: network port of the server host to connect to. Defaults to
        1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you
        are using tls_set() the port may need providing.
        @type port: int
        @param keepalive: Maximum period in seconds between communications with the
        @type keepalive: int
        @param bind_address: Maximum period in seconds between communications with the
        broker. If no other messages are being exchanged, this controls the
        rate at which the client will send ping messages to the broker.
        @type bind_address: str
        @return: connection result
        @rtype: int
        """
        return super().connect(
            host=host or self.config.broker,
            port=port or self.config.port,
            keepalive=keepalive,
            bind_address=bind_address
        )

    def single(
            self, topic, payload=None, qos=1, retain=True, hostname=None,
            port=None, client_id="", keepalive=60, will=None, auth=None,
            tls=None, protocol=MQTTv311, transport="tcp"
    ):
        """
        paho.mqtt.publish.single method
        """
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        publish.single(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            hostname=self.config.broker if self.config else hostname,
            port=self.config.port if self.config else port,
            client_id=self._client_id if self.config else client_id,
            keepalive=keepalive,
            will=will,
            auth=auth,
            tls=tls,
            protocol=protocol,
            transport=transport
        )

    def __repr__(self):
        """
        @rtype: str
        """
        return f"{self.config.client_id} ({self.config.broker}:{self.config.port})"
