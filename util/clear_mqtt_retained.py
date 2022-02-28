from library.communication.mqtt import MQTTClient

client = MQTTClient("retain_clear")
host = "192.168.1.18"
port = 1883
retain = True
qos = 2
msg = None
topics = [f"hass/env/00{x}" for x in range(6)]

for topic in topics:
    print(f"clearing retained messages on: {host}:{port} - {topic}")
    client.single(topic, msg, qos, retain, host, port, "retain_clear")

