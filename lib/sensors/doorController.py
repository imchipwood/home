'''Threaded MQTT Door Control and State Monitoring

Chip Wood, Jan. 2017

This file is a one-stop shop for reading the state of a door as well as
controlling the door, through the use of two GPIO pins and an MQTT connection.

A state monitoring MQTT client thread reads the state sensor at 1Hz.
When the state changes, the new state is published on an MQTT topic.
The published states are "open" and "closed".

A separate control MQTT client thread subscribes to the control topic and
toggles the GPIO when a message is published with the payload of "TOGGLE".
It does not respond to any other messages.
'''
import os
import logging
import RPi.GPIO as GPIO
import paho.mqtt.client as paho
import timeit
from time import sleep
from multiprocessing import Process

# logging junk
# Level	    Numeric value
# CRITICAL	 50
# ERROR	    40
# WARNING	  30
# INFO	     20
# DEBUG	    10
# NOTSET	    0

# TODO: MQTT - need to set up a periodic conversation
# client sends message to "keepalive" topic, expects specific response
#   if response is received, continue
#   if response is not received, attempt to reconnect and try "keepalive" again
# do this... every 15 minutes? need to screw around with it


class Error(Exception):
    pass


class MQTTError(Error):
    pass


'''Threaded Door Controller object

This class is intended to handle all aspects of door monitoring and control.

Inputs:
    - configFile        the full system path to a configuration file
    - debug             Boolean to enable more verbose logging. Default: false

Once instantiated, simply call the start() method to launch the threads
'''
class DoorController(object):

    config = {}
    clientState = ""
    clientControl = ""
    state = False

    def __init__(self, configFile, debug=False):
        super(DoorController, self).__init__()
        self.bDebug = debug

        if os.path.exists(configFile):
            self.sConfigFile = configFile
        else:
            raise IOError()
    
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # formatting - add this to han
        stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
        fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        stdoutFormatter = logging.Formatter(stdoutFormat)
        fileFormatter = logging.Formatter(fileFormat)
        # stdout handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(stdoutFormatter)
        self.logger.addHandler(ch)
        
        self.monitorThread = Process(target=self.monitor, args=[])
        self.controlThread = Process(target=self.control, args=[])

        if self.readConfig():
            # set up file handler for logger
            self.log = self.__config["log"]
            fh = logging.FileHandler(self.log)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(fileFormatter)
            self.logger.addHandler(fh)

            # pull MQTT stuff out of config
            try:
                self.mqttClient = self.__config["mqtt_client"]
                self.mqttBroker = self.__config["mqtt_broker"]
                self.mqttPort = self.__config["mqtt_port"]
                self.mqttTopicState = self.__config["mqtt_topic_state"]
                self.mqttTopicControl = self.__config["mqtt_topic_control"]
                self.logger.debug("mqttClient: {}".format(self.mqttClient))
                self.logger.debug("mqttBroker: {}".format(self.mqttBroker))
                self.logger.debug("mqttPort: {}".format(self.mqttPort))
                self.logger.debug("mqttTopicState: {}".format(self.mqttTopicState))
                self.logger.debug("mqttTopicControl: {}".format(self.mqttTopicControl))
            except:
                self.logger.exception("Error with MQTT config")
                raise Exception()

            # pull GPIO stuff out of config and set up GPIO
            try:
                GPIO.setmode(GPIO.BCM)
                # sensor
                self.pinSensor = self.__config["pin_sensor"]
                # TODO: add ability to configure as pull-up or pull-down
                GPIO.setup(self.pinSensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.getState()  # initialize sensor

                # control
                self.pinControl = self.__config["pin_control"]
                GPIO.setup(self.pinControl, GPIO.OUT)
                self.off()  # ensure control output is LOW
            except:
                self.logger.exception("Error with Sensor/Relay config")
                raise Exception()
        else:
            raise IOError("Failed to read config")
        return

###############################################################################

    '''Start the state monitoring and control threads
    This function initializes all MQTT connections and subscriptions
    and launches separate Processes for each
    '''
    def start(self):
        try:
            self.logger.debug("starting state mqtt connection")
            #self.stateConnect()
            self.logger.debug("starting state thread")
            self.monitorThread.start()
        except:
            self.logger.exception("failed to start state thread")
            self.cleanup()
            raise
        # launch control thread
        try:
            self.logger.debug("starting control mqtt connection")
            self.controlConnect()
            self.logger.debug("starting control thread")
            self.controlThread.start()
        except:
            self.logger.exception("failed to start control thread")
            self.cleanup()
            raise
        return

###############################################################################
    '''Read configuration from a file

    Expected tokens:
        log - full path of file to log to
        mqtt_client - name to send MQTT messages as
        mqtt_broker - IP address of MQTT broker
        mqtt_port - port to talk to MQTT broker on
        mqtt_topic_state - MQTT topic to send state updates on
        mqtt_topic_control - MQTT topic to listen for commands on
        pin_sensor - GPIO # that door is connected to
        pin_control - GPIO # that relay is connected to
    '''
    def readConfig(self):
        config = {}
        with open(self.sConfigFile, "r") as inf:
            for line in inf:
                line = line.rstrip().split("=")
                key = line[0]
                val = line[1]
                if key in ["pin_sensor", "pin_control", "mqtt_port"]:
                    val = int(val)
                config[key] = val
                if self.bDebug:
                    self.logger.debug("-d- config: key:val '{}:{}'".format(key,
                                                                           val)
                                      )
        bConfigValid = True
        for key in config.keys():
            if "pin" in key:
                if 2 > config[key] > 27:
                    bConfigValid = False
        if bConfigValid:
            self.__config = config
        return bConfigValid

###############################################################################
# GPIO interactions

    def on(self):
        if self.bDebug:
            self.logger.debug("control - on")
        GPIO.output(self.pinControl, GPIO.HIGH)
        return

    def off(self):
        if self.bDebug:
            self.logger.debug("control - off")
        GPIO.output(self.pinControl, GPIO.LOW)
        return

    def toggle(self):
        self.on()
        sleep(0.3)
        self.off()
        return

    def getState(self):
        return GPIO.input(self.pinSensor)

###############################################################################
# looping functions - these two functions are intended to be launched
#                     in individual threads

    def control(self):
        self.clientControl.loop_forever()  # blocking
        return

    def monitor(self):
        oneHz = 1.0
        lastOneHzTime = 0
        lastDoorState = -99

        while True:
            now = float(timeit.default_timer())
            if (now - lastOneHzTime) > oneHz:
                lastOneHzTime = now
                try:
                    newState = self.getState()
                    if newState != lastDoorState:
                        lastDoorState = newState
                        self.state = newState
                        if self.bDebug:
                            self.logger.debug("monitor state: %s" % (self.state))
                        # TODO: add ability to configure N.O. vs N.C.
                        if self.state:
                            self.publish("open")
                        else:
                            self.publish("closed")
                except:
                    self.logger.exception("state exception")
                    raise

###############################################################################
# Connection and cleanup functions

    def controlConnect(self):
        if self.bDebug:
            self.logger.debug("control connect")
        self.clientControl = paho.Client(client_id=self.mqttClient)
        self.clientControl.on_connect = self.on_connect
        self.clientControl.on_subscribe = self.on_subscribe
        self.clientControl.on_message = self.on_message
        self.clientControl.connect(self.mqttBroker, self.mqttPort)
        self.clientControl.subscribe(self.mqttTopicControl, qos=2)
        return

    def stateConnect(self):
        if self.bDebug:
            self.logger.debug("state connect")
        self.clientState = paho.Client(client_id=self.mqttClient)
        self.clientState.on_connect = self.on_connect
        self.clientState.on_publish = self.on_publish
        self.clientState.connect(host=self.mqttBroker,
                                 port=self.mqttPort,
                                 keepalive=10)
        self.clientState.loop_start()  # non-blocking
        sleep(3)
        return

    def mqttCleanup(self):
        #try:
        #    self.clientState.loop_stop()
        #    self.clientState.unsubscribe(self.mqttTopicState)
        #    self.clientState.disconnect()
        #except:
        #    self.logger.exception("mqttCleanup clientState exception")
        #    pass
        try:
            self.clientControl.loop_stop()
            self.clientControl.unsubscribe(self.mqttTopicControl)
            self.clientControl.disconnect()
        except:
            self.logger.exception("mqttCleanup clientControl exception")
            pass
        return

    def cleanup(self):
        self.logger.info("cleaning up")
        try:
            self.monitorThread.terminate()
            self.controlThread.terminate()
        except:
            pass
        GPIO.cleanup()
        self.mqttCleanup()
        return

###############################################################################
# MQTT interaction functions

    def publish(self, data):
        # first create the connection
        #if self.bDebug:
        #    self.logger.debug("state connect")
        #self.clientState = paho.Client(client_id=self.mqttClient)
        #self.clientState.on_connect = self.on_connect
        #self.clientState.on_publish = self.on_publish
        #self.clientState.connect(host=self.mqttBroker,
        #                         port=self.mqttPort,
        #                         keepalive=10)
        #self.clientState.loop_start()  # non-blocking
        #sleep(2)
        self.stateConnect()
        # then publish the message
        if self.bDebug:
            self.logger.debug("mqtt: pub '{}' to topic '{}'".format(data, self.mqttTopicState))
        (rc, mid) = self.clientState.publish(self.mqttTopicState,
                                             str(data),
                                             qos=2,
                                             retain=True)
        self.logger.info("mqtt: pub rc, mid = {}, {}".format(rc, mid))
        # clean up
        self.clientState.loop_stop()
        self.clientState.unsubscribe(self.mqttTopicControl)
        self.clientState.disconnect()
        return

    def on_connect(self, client, userdata, flags, rc):
#        if self.bDebug:
#            self.logger.debug("mqtt: (CONNECTION) received with code {}".format(rc))
        # MQTTCLIENT_SUCCESS = 0, all others are some kind of error.
        # attempt to reconnect on errors
        if rc != 0:
            if rc == -4:
                self.logger.exception("mqtt: ERROR: 'too many messages'\n")
            elif rc == -5:
                self.logger.exception("mqtt: ERROR: 'invalid UTF-8 string'\n")
            elif rc == -9:
                self.logger.exception("mqtt: ERROR: 'bad QoS'\n")
            raise MQTTError("on_connect 'rc' failure")
        return

    def on_subscribe(self, client, userdata, mid, granted_qos):
        if self.bDebug:
            self.logger.debug("mqtt: (SUBSCRIBE) mid: {}, granted_qos: {}".format(mid,
                                                                                  granted_qos))
        return

    def on_publish(self, client, userdata, mid):
        if self.bDebug:
            self.logger.debug("mqtt: (PUBLISH) mid: {}".format(mid))
        return

    def on_message(self, client, userdata, msg):
        if self.bDebug:
            self.logger.debug("mqtt: (RX) topic: {}, QOS: {}, payload: {}".format(msg.topic,
                                                                                  msg.qos,
                                                                                  msg.payload))
        if msg.topic == self.mqttTopicControl and msg.payload == "TOGGLE":
            self.toggle()
        return
