import json
from paho.mqtt.client import Client, MQTTv311
from paho.mqtt import publish

from library.config.mqtt import MQTTConfig


class MQTTClient(Client):
	def __init__(self, client_id="", clean_session=True, userdata=None, protocol=MQTTv311, transport="tcp", mqtt_config=None):
		"""
		@type mqtt_config: MQTTConfig
		"""
		self.config = mqtt_config
		if mqtt_config:
			super(MQTTClient, self).__init__(
				client_id=self.config.client_id,
				clean_session=clean_session,
				userdata=userdata,
				protocol=protocol,
				transport=transport
			)
		else:
			super(MQTTClient, self).__init__(
				client_id=client_id,
				clean_session=clean_session,
				userdata=userdata,
				protocol=protocol,
				transport=transport
			)

	def connect(self, host="", port=1883, keepalive=60, bind_address=""):
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
		return super(MQTTClient, self).connect(
			host=host or self.config.broker,
			port=port or self.config.port,
			keepalive=keepalive,
			bind_address=bind_address
		)

	def single(self, topic, payload=None, qos=1, retain=True, hostname=None,
			port=None, client_id="", keepalive=60, will=None, auth=None,
			tls=None, protocol=MQTTv311, transport="tcp"):
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
			hostname=hostname or self.config.broker,
			port=port or self.config.port,
			client_id=client_id or self._client_id,
			keepalive=keepalive,
			will=will,
			auth=auth,
			tls=tls,
			protocol=protocol,
			transport=transport
		)
