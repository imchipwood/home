import paho.mqtt.client as paho
from time import sleep
 
def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code %d." % (rc))


def on_publish(client, userdata, mid):
    print("mid: "+str(mid))


mqttHost = "192.168.1.130"
mqttPort = 1883
mqttTopic = "home-assistant/garage/door"

client = paho.Client(client_id="garageDoor")
client.on_connect = on_connect
client.on_publish = on_publish
client.connect(mqttHost, mqttPort)
client.loop_start()
sleep(3)

(rc, mid) = client.publish(mqttTopic, "0", qos=1)
rc
mid

client.loop_stop()
client.unsubscribe(mqttTopic)
client.disconnect()
