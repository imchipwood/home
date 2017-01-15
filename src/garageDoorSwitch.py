#!/usr/bin/python
import argparse
import traceback
import RPi.GPIO as GPIO
import paho.mqtt.client as paho
from time import sleep

# globals
global sHomePath
global endThreads

# # stupidity until I figure out how to package my libs properly
# import sys
# import os
# sHomePath = os.path.dirname(os.path.realpath(__file__))
# sHomePath = "/".join(sHomePath.split("/")[:-1])
# while "home" not in sHomePath.split("/")[-1]:
#     sHomePath = "/".join(sHomePath.split("/")[:-1])
# sys.path.append(sHomePath+"/lib/actuators")
# from actuator_relay import Relay


def parseArgs():
    # argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-configFile",
                        "-c",
                        type=str,
                        default="garageSwitch.txt",
                        help="Config file for pin setup and MQTT info")
    parser.add_argument('-debug',
                        '-d',
                        action="store_true",
                        help="Enable debug messages")

    args = parser.parse_args()
    return args


# read config file
# expected keys:
#   relay_pin       - GPIO pin # for opening/closing door
#   mqtt_client     - name for the client
#   mqtt_broker     - IP address of MQTT broker
#   mqtt_port       - Port to use for MQTT broker
#   mqtt_topic      - topic to listen to for open/close commands
def readConfig(f, bDebug):
    if bDebug:
        print "-d- Using config file found here:"
        print "-d- {}".format(f)
    config = {}
    with open(f, "r") as inf:
        for line in inf:
            line = line.rstrip().split("=")
            key = line[0]
            val = line[1]
            if key in ["relay_pin", "mqtt_port"]:
                val = int(val)
            config[key] = val
            if bDebug:
                print "-d- config: found key {} with val {}".format(key, val)
    return config


class MQTTRelay(object):

    def __init__(self, config, bDebug):
        super(MQTTRelay, self).__init__()
        
        # set up pin and drive low
        GPIO.setmode(GPIO.BCM)
        self.pin = config["relay_pin"]
        if bDebug:
            print("MQTTRelay - setting up pin: {}".format(self.pin))
        GPIO.setup(self.pin, GPIO.OUT)
        self.off()
        
        self.mqttClientId = config["mqtt_client"]
        self.mqttHost = config["mqtt_broker"]
        self.mqttPort = config["mqtt_port"]
        self.mqttTopic = config["mqtt_topic"]

    def start(self):
        if bDebug:
            print("MQTTRelay - iniitializing mqtt connection")
        self.client = paho.Client(client_id=self.mqttClientId)
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.client.connect(self.mqttHost, self.mqttPort)
        self.client.subscribe(self.mqttTopic, qos=1)
        try:
            self.client.loop_forever()
        except:
            self.cleanup()
            raise
        return

    def on_connect(self, client, userdata, flags, rc):
        print("mqtt: CONNACK received with code %d." % (rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("mqtt: Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_message(self, client, userdata, msg):
        print("mqtt: rx: "+msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        self.toggle()

    def cleanup(self):
        if bDebug:
            print("MQTTRelay - cleaning up...")
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.unsubscribe(self.mqttTopic)
        self.client.disconnect()

    def on(self):
        if bDebug:
            print("MQTTRelay - on")
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        if bDebug:
            print("MQTTRelay - off")
        GPIO.output(self.pin, GPIO.LOW)

    def toggle(self):
        if bDebug:
            print("MQTTRelay - toggle")
        self.on()
        if bDebug:
            print("MQTTrelay - sleep")
        sleep(0.3)
        self.off()

    @property
    def state(self):
        return GPIO.input(self.pin)


def main():
    parsedArgs = parseArgs()
    sConfigFile = parsedArgs.configFile
    bDebug = parsedArgs.debug

    dConfig = readConfig(sConfigFile, bDebug)
    try:
        gdr = MQTTRelay(dConfig, bDebug)
    except:
        raise
    try:
        gdr.start()
    except KeyboardInterrupt:
        print("\n\t-e- gd: KeyboardInterrupt, exiting gracefully\n")
    except Exception as e:
        print("\n\t-E- gd: Some exception: %s\n" % (e))
        traceback.print_exc()
        raise e
    return


if __name__ == '__main__':
    main()
