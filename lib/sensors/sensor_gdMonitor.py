import os
import sys
from numpy import interp
from multiprocessing import Process
import timeit
import RPi.GPIO as GPIO
from sensor import Sensor
from time import sleep



import paho.mqtt.client as paho
import paho.mqtt.publish as publish



# stupidity until I figure out how to package my libs properly
global sHomePath
sHomePath = os.path.dirname(os.path.realpath(__file__))
sHomePath = "/".join(sHomePath.split("/")[:-1])
while "home" not in sHomePath.split("/")[-1]:
    sHomePath = "/".join(sHomePath.split("/")[:-1])


def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code %d." % (rc))


def on_publish(client, userdata, mid):
    print("mid: "+str(mid))


class GarageDoorMonitor(Sensor):
    """Garage Door Monitor Class

    This class houses all functions required monitor the state
    of a garage door.

    Types of sensors to support:
    1. Rotary Encoder (attached to motor, detect rotations)
    2. Limit switch(es) - top and bottom to detect only fully open and closed
    """
    sensorType = {
        "rotary": False,
        "limitOpen": False,
        "limitClosed": False
    }
    pins = {
        "rotary": None,
        "limitOpen": None,
        "limitClosed": None
    }
    limitStates = {
        "open": False,
        "closed": False
    }
    rotaryLimits = {
        "open": 100,
        "closed": 0
    }
    rotaryCount = 0
    bDebug = False
    doorState = -1
    db = ""

    # MQTT
    mqttHost = "0.0.0.0"
    mqttPort = 0
    mqttTopic = ""
    client = ""

    """Initialize a Garage Door Monitor

    Inputs:
        f - name of file to read config from
        debug (Boolean)
    Returns:
        Nothing
    """
    def __init__(self, f, debug=False):
        super(GarageDoorMonitor, self).__init__()
        self.bDebug = debug
        GPIO.setmode(GPIO.BCM)

        # read config file
        if os.path.exists(f):
            self.sConfFile = f
        else:
            print("-E- gdMonitor: Check if file exists: {}".format(f))
            raise IOError()

        if self.readConfig():

            if self.bDebug:
                self.printConfig()

            # setup connection to mqtt broker
            self.mqttSetup()

            # determine sensor type
            self.enableSensors()

            # read limit switches to initialize states
            self.readLimitSwitches()

            try:
                # begin monitoring sensors
                self.monitorThread = Process(target=self.monitor, args=[])
                self.monitorThread.start()
            except:
                self.cleanup()
                raise

###############################################################################

    """Read config file

    Inputs:
        None
    Returns:
        True if config was read and is valid, False otherwise
    """
    def readConfig(self):
        tmpPins = self.pins
        with open(self.sConfFile, "r") as inf:
            for line in inf:
                line = line.rstrip().split("=")
                # attempt to convert value to int but ignore fails
                # value might be a string for some other config (DB, etc.)
                try:
                    iPinNum = int(line[-1])
                except:
                    pass
                # gpio
                if line[0] == "plo":
                    tmpPins["limitOpen"] = iPinNum
                if line[0] == "plc":
                    tmpPins["limitClosed"] = iPinNum
                if line[0] == "pro":
                    tmpPins["rotary"] = iPinNum
                # mqtt config
                if line[0] == "h":
                    self.mqttHost = str(line[-1])
                if line[0] == "p":
                    self.mqttPort = int(line[-1])
                if line[0] == "t":
                    self.mqttTopic = str(line[-1])
        validConf = True
        for pin in tmpPins:
            if 2 > pin > 27:  # valid RPi GPIO pins are 2-27
                validConf = False
        if validConf:
            self.pins = tmpPins
        return validConf

###############################################################################

    def printConfig(self):
        if self.bDebug:
            print("-d- garageDoor config")
            print("-d- pin: limitOpen   : {}".format(self.pins["limitOpen"]))
            print("-d- pin: limitClosed : {}".format(self.pins["limitClosed"]))
            print("-d- pin: rotary      : {}".format(self.pins["rotary"]))
            print("-d- mqtt: host       : {}, {}".format(self.mqttHost,
                                                         type(self.mqttHost)))
            print("-d- mqtt: port       : {}, {}".format(self.mqttPort,
                                                         type(self.mqttPort)))
            print("-d- mqtt: topic      : {}, {}".format(self.mqttTopic,
                                                         type(self.mqttTopic)))
        return

###############################################################################

    def mqttSetup(self):
        #self.client = paho.Client(client_id="garageDoorMonitor")
        #self.client.on_connect = on_connect
        #self.client.on_publish = on_publish
        #self.client.connect(self.mqttHost, self.mqttPort)
        #self.client.loop_start()
        #sleep(3) # wait time for client to connect
        #if self.bDebug:
        #    print("-d- mqtt client: {}".format(self.client))
        return

###############################################################################
    
    def mqttPublish(self, data):
        if self.bDebug:
            print("-d- mqtt publishing data: {}".format(data))
        #(rc, mid) = publish.single(topic=self.mqttTopic, payload=str(data),
        publish.single(topic=self.mqttTopic, payload=str(data),
                                   qos=2, hostname=self.mqttHost,
                                   port=self.mqttPort,
                                   client_id="garageDoorMonitor")
        #(rc, mid) = self.client.publish(self.mqttTopic, str(data), qos=1)
        if self.bDebug:
            print("-d- mqtt topic:  {}".format(self.mqttTopic))
            print("-d- mqtt port:   {}".format(self.mqttPort))
            #print("-d- mqtt rc/mid: {}/{}".format(rc, mid))
            print("-d- mqtt client: {}".format(self.client))
        return

###############################################################################

    """Enable sensors

    Sets up GPIO pins for all sensors
    Defaults to pull-up

    Inputs:
        sensors - dict of sensors to enable
    Returns:
        Nothing, but does throw exception if it fails
    """
    def enableSensors(self):
        for pin in self.pins:
            if self.pins[pin] is not None:
                self.sensorType[pin] = True
                if self.bDebug:
                    s = "{}: pin {}".format(pin, self.pins[pin])
                    print("-d- gdMonitor: {}".format(s))
                # TODO - enable selection of pull-up or pull-down resistor
                GPIO.setup(self.pins[pin],
                           GPIO.IN,
                           pull_up_down=GPIO.PUD_UP)
        return

###############################################################################

    """Clean up GPIO

    Inputs:
        None
    Returns:
        Nothing
    """
    def cleanup(self):
        self.monitorThread.terminate()
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.unsubscribe(self.mqttTopic)
        self.client.disconnect()
        return

###############################################################################

    """Monitor thread

    This function is intended to be launched as a thread to read sensors
    on a one second interval and update database with new data. Will update
    database when first launched

    Inputs:
        endThreads - a boolean to exit all threads
    Returns:
        Nothing
    """
    def monitor(self):
        onehz = 1.0
        lastonehztime = 0
        lastDoorState = -99
        while True:
            now = float(timeit.default_timer())
            if (now - lastonehztime) > onehz:
                lastonehztime = now
                try:
                    self.read()
                    dState = self.getDoorState()
                    if dState != lastDoorState:
                        lastDoorState = dState
                        if self.bDebug:
                            print("-d- gdMonitor: state changed: {}".format(dState))
                        if 0 <= dState <= 100:
                            self.mqttPublish(dState)
                        else:
                            if self.bDebug:
                                print("-d- gdMonitor: door state invalid")
                except:
                    if self.bDebug:
                        print("-d- gdMonitor: thread exception")
                    raise
        return

###############################################################################

    """Take readings

    If limit switches are enabled, it also calls the rotary calibration
    function to ensure the rotary limits are set up properly

    Inputs:
        None
    Returns:
        Nothing
    """
    def read(self):
        self.readLimitSwitches()
        self.readRotaryEncoder()
        self.calcDoorState()
        return

###############################################################################

    """Return current state

    Inputs:
        None
    Returns:
        self.
    """
    def getDoorState(self):
        return self.doorState

###############################################################################

    """Read Rotary Encoder

    Inputs:
        None
    Returns:
        integer between 0-100 representing % door is open
    """
    def readRotaryEncoder(self):
        # read pins["rotary"]
        if self.sensorType["rotary"]:
            if self.bDebug:
                print("-d- gdMonitor: reading rotary encoder")
            self.updateRotaryCalibration()
        return

###############################################################################

    """Read limit switches

    Inputs:
        None
    Returns:
        Nothing
    """
    def readLimitSwitches(self):
        tmp = self.limitStates
        if self.sensorType["limitOpen"]:
            tmp["open"] = not GPIO.input(self.pins["limitOpen"])
            if self.bDebug:
                print("-d- gdMonitor: switch open: {}".format(tmp["open"]))
        if self.sensorType["limitClosed"]:
            tmp["closed"] = not GPIO.input(self.pins["limitClosed"])
            if self.bDebug:
                print("-d- gdMonitor: switch closed: {}".format(tmp["closed"]))
        self.limitStates = tmp
        return

###############################################################################

    """On the fly rotary calibration

    When a limit switch is triggered, this means the door is either fully
    closed or fully open. We can use this info to make sure the rotary
    encoder count limits are up to date.

    If CLOSED limit switch is True, can reset the rotary count to 0
    If OPEN limit switch is True, the current rotary count is
        the maximum limit. Update the maximum limit.

    Inputs:
        None
    Returns:
        True if no issues, False otherwise
    """
    def updateRotaryCalibration(self):
        if self.sensorType["limitOpen"] or self.sensorType["limitClosed"]:
            if self.bDebug:
                print("-d- gdMonitor: rotary calib")
            if self.limitStates["open"] and self.limitStates["closed"]:
                return False
            elif self.limitStates["open"]:
                if self.bDebug:
                    print("-d- gdMonitor: rotary calib - new 'open' limit")
                rotaryLimits["open"] = self.rotaryCount
            elif self.limitStates["closed"]:
                self.rotaryCount = 0
                if self.bDebug:
                    print("-d- gdMonitor: rotary calib - reset counter")
        return True

###############################################################################

    """Calculate state of garage door

    Inputs:
        None
    Returns:
        integer between 0-100 representing % door is open
    """
    def calcDoorState(self):
        doorState = 0
        limitState = False
        # priority is given to limit switches
        # if a limit switch is ON, the door is either fully open or closed
        # don't bother using the rotary encoder in this case
        if self.sensorType["limitOpen"] or self.sensorType["limitClosed"]:
            # check for error state
            if self.limitStates["open"] and self.limitStates["closed"]:
                return -999
            elif self.limitStates["open"] or self.limitStates["closed"]:
                limitState = True
                doorState = 0 if self.limitStates["closed"] else 100
            elif True not in [self.limitStates["open"],
                              self.limitStates["closed"]]:
                # if no switch is touched, door must be open. set to a # that
                # doesn't represent open or closed
                doorState = 50
        # only use rotary encoder count if neither limit switch was ON
        if self.sensorType["rotary"] and not limitState:
            doorState = int(interp(self.rotaryCount,
                                   [self.rotaryLimits["closed"],
                                    self.rotaryLimits["open"]],
                                   [0, 100]
                                   )
                            )
        self.doorState = doorState
        return

###############################################################################

    """Get current units

    Not relevant until rotary encoder is enabled
    No way to tell distance without it

    Inputs:
        None
    Returns:
        Nothing
    """
    def getUnits(self):
        return

###############################################################################

    """Update sensor units

    Inputs:
        units - whatever you want, it's unused for now
    Returns:
        Nothing
    """
    def setUnits(self, units):
        return

###############################################################################
