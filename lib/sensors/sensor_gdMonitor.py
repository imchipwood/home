import os
from numpy import interp
from multiprocessing import Process
import timeit
import RPi.GPIO as GPIO
from sensor import Sensor


class GarageDoorMonitor(Sensor):
    """Garage Door Monitor Class

    This class houses all functions required monitor the state
    of a garage door.

    Types of sensors to support:
    1. Rotary Encoder (attached to motor, detect rotations)
    2. Limit switch(es) - top and bottom to detect only fully open and closed
    """
    validSensorTypes = ["rotary", "limitOpen", "limitClosed"]
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
    doorState = ""

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
            print "-E- HomeDB: Check if file exists: {}".format(f)
            raise IOError()

        if self.readConfig():

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
                if line[0] == "plo":
                    tmpPins["limitOpen"] = iPinNum
                if line[0] == "plc":
                    tmpPins["limitClosed"] = iPinNum
                if line[0] == "pro":
                    tmpPins["rotary"] = iPinNum
        validConf = True
        for pin in tmpPins:
            if 2 > pin > 27:  # valid RPi GPIO pins are 2-27
                validConf = False
        if validConf:
            self.pins = tmpPins
        return validConf

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
                    print "-d- gdMonitor: %s" % s
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
        return

###############################################################################

    """Monitor thread

    This function is intended to be launched as a thread to read sensors
    on a one second interval

    Inputs:
        endThreads - a boolean to exit all threads
    Returns:
        Nothing
    """
    def monitor(self):
        onehz = 1.0
        lastonehztime = 0
        while True:
            now = float(timeit.default_timer())
            if (now - lastonehztime) > onehz:
                lastonehztime = now
                if self.bDebug:
                    print "-d- gdMonitor: thread executing"
                try:
                    self.read()
                    if self.bDebug:
                        print ("-d- gdMonitor: thread state: {}".format(
                               self.getDoorState())
                               )
                except:
                    if self.bDebug:
                        print "-d- gdMonitor: thread exception"
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
                print "-d- gdMonitor: reading rotary encoder"
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
                print "-d- gdMonitor: switch open: {}".format(tmp["open"])
        if self.sensorType["limitClosed"]:
            tmp["closed"] = not GPIO.input(self.pins["limitClosed"])
            if self.bDebug:
                print "-d- gdMonitor: switch closed: {}".format(tmp["closed"])
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
                print "-d- gdMonitor: rotary calib"
            if self.limitStates["open"] and self.limitStates["closed"]:
                return False
            elif self.limitStates["open"]:
                if self.bDebug:
                    print "-d- gdMonitor: rotary calib - new 'open' limit"
                rotaryLimits["open"] = self.rotaryCount
            elif self.limitStates["closed"]:
                self.rotaryCount = 0
                if self.bDebug:
                    print "-d- gdMonitor: rotary calib - reset counter"
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
