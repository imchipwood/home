import argparse
import paho.mqtt.client as paho
from time import sleep


def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code %d." % (rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))


parser = argparse.ArgumentParser()
parser.add_argument("-client_id",
                    "-c",
                    type=str,
                    default="test",
                    help="client_id for MQTT connection")
args = parser.parse_args()

mqttHost = "192.168.1.130"
mqttPort = 1883
mqttTopic = "home-assistant/test/pub"

print("mqtthost: {}".format(mqttHost))
print("mqttPort: {}".format(mqttPort))
print("mqttTopic: {}".format(mqttTopic))

client = paho.Client(client_id=args.client_id)
client.on_subscribe = on_subscribe
client.on_message = on_message
client.connect(mqttHost, mqttPort)
client.subscribe(mqttTopic, qos=1)
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("keyboard interrupt detected, exiting gracefully")
finally:
    client.loop_stop()
    client.unsubscribe(mqttTopic)
    client.disconnect()
