#!/usr/bin/python
import os
import argparse
import traceback
import RPi.GPIO as GPIO
import paho.mqtt.client as paho
from time import sleep, time
from datetime import datetime


###############################################################################
# Appetizers
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


class Error(Exception):
    pass


class MQTTError(Error):
    pass


class MQTTRelay(object):
    '''Relay Object with MQTT Support

    This class encapsulates simple functions to set up and drive a relay/switch
    It drives a relay based on messages detected via an MQTT subscription.
    The class subscribes to an MQTT topic and whenever a message is detected,
    it toggles the relay.
    '''
    def __init__(self, f, bDebug):
        super(MQTTRelay, self).__init__()
        self.bDebug = bDebug

        self.dConfig = self.readConfig(f)

        # set up pin and drive low
        GPIO.setmode(GPIO.BCM)
        self.pin = self.dConfig["relay_pin"]
        if self.bDebug:
            print("MQTTRelay - setting up pin: {}".format(self.pin))
        GPIO.setup(self.pin, GPIO.OUT)
        self.off()

        # MQTT info
        self.mqttClientId = self.dConfig["mqtt_client"]
        self.mqttHost = self.dConfig["mqtt_broker"]
        self.mqttPort = self.dConfig["mqtt_port"]
        self.mqttTopic = self.dConfig["mqtt_topic"]
        return

    '''Read Config - setup

    expected keys:
      relay_pin       - GPIO pin # for opening/closing door
      mqtt_client     - name for the client
      mqtt_broker     - IP address of MQTT broker
      mqtt_port       - Port to use for MQTT broker
      mqtt_topic      - topic to listen to for open/close commands
      log             - path to file to log info to
    '''
    def readConfig(self, f):
        if self.bDebug:
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
                if self.bDebug:
                    print "-d- config: found key:val '{}:{}'".format(key, val)
        return config

    # return formatted timestamp
    def getTimeStamp(self):
        return datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')

    # put stuff in log file with timestamp
    def printToLog(self, s):
        fileMode = "a"
        s = self.getTimeStamp() + " - " + s
        if not os.path.exists(self.dConfig["log"]):
            fileMode = "w"
        with open(self.dConfig["log"], fileMode) as ouf:
            ouf.write(s)
        return

    ###########################################################################
    # Relay functionality
    def on(self):
        if self.bDebug:
            print("MQTTRelay - on")
        GPIO.output(self.pin, GPIO.HIGH)
        return

    def off(self):
        if self.bDebug:
            print("MQTTRelay - off")
        GPIO.output(self.pin, GPIO.LOW)
        return

    def toggle(self):
        self.on()
        sleep(0.3)
        self.off()
        return

    @property
    def state(self):
        return GPIO.input(self.pin)

    ###########################################################################
    # MQTT functionality

    '''setup MQTT connection
    Sets up MQTT client, attaches connect/subscribe/message functions to the
    client, subscribes to a topic
    '''
    def connect(self):
        if self.bDebug:
            print("MQTTRelay - iniitializing mqtt connection")
        self.client = paho.Client(client_id=self.mqttClientId)
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.client.connect(self.mqttHost, self.mqttPort)
        self.client.subscribe(self.mqttTopic, qos=1)
        return

    '''start MQTT loop
    Blocking function that loops until the process is stopped
    '''
    def start(self):
        try:
            self.client.loop_forever()
        except:
            self.mqtt_cleanup()
            raise
        return

    '''Print out some info any time a connection is made
    '''
    def on_connect(self, client, userdata, flags, rc):
        s = "mqtt: (CONNECTION) received with code {}.".format(rc)
        if self.bDebug:
            print(s)
        # MQTTCLIENT_SUCCESS = 0, all others are some kind of error.
        # attempt to reconnect on errors
        if rc != 0:
            self.printToLog(s+"\n")
            if rc == -4:
                self.printToLog("mqtt: ERROR: 'too many messages in flight'\n")
            elif rc == -5:
                self.printToLog("mqtt: ERROR: 'invalid UTF-8 string'\n")
            elif rc == -9:
                self.printToLog("mqtt: ERROR: 'bad QoS'\n")
            raise MQTTError("on_connect 'rc' failure")
        return

    '''Print out some info any time a subscription is made
    '''
    def on_subscribe(self, client, userdata, mid, granted_qos):
        s = "mqtt: (SUBSCRIBE) mid: {}, granted_qos: {}".format(mid,
                                                                  granted_qos)
        if self.bDebug:
            print(s)
        self.printToLog(s+"\n")
        return

    '''Print out some info any time a message is received
    '''
    def on_message(self, client, userdata, msg):
        s = "mqtt: (RX) topic: {}, QOS: {}, payload: {}".format(msg.topic,
                                                                  msg.qos,
                                                                  msg.payload)
        if self.bDebug:
            print(s)
        self.printToLog(s+"\n")
        self.toggle()
        return

    def mqtt_cleanup(self):
        try:
            self.client.loop_stop()
            self.client.unsubscribe(self.mqttTopic)
            self.client.disconnect()
        except:
            pass

    ###########################################################################
    # Clean up GPIO & MQTT connections
    def cleanup(self):
        if self.bDebug:
            print("MQTTRelay - cleaning up...")
        GPIO.cleanup()
        self.mqtt_cleanup()
        return


###############################################################################
# Entrees
def main():
    parsedArgs = parseArgs()
    sConfigFile = parsedArgs.configFile
    bDebug = parsedArgs.debug

    try:
        gdr = MQTTRelay(sConfigFile, bDebug)
    except:
        raise
    try:
        while True:
            try:
                gdr.connect()
                gdr.start()
            except MQTTError:
                pass
    except KeyboardInterrupt:
        print("\n\t-e- KeyboardInterrupt, exiting gracefully\n")
    except Exception as e:
        print("\n\t-E- Some exception: %s\n" % (e))
        traceback.print_exc()
        gdr.printToLog("-e- EXCEPTION:\n{}\n".format(e))
        raise e
    finally:
        gdr.cleanup()
        gdr.printToLog("exiting");
    return


if __name__ == '__main__':
    main()
