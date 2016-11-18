from numpy import interp
import RPi.GPIO as GPIO
from sensor import Sensor, SensorException


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

    """Initialize a Garage Door Monitor

    Inputs:
        sensorTypes - array of strings
        pins - dict with keys "rotary", "limitClosed", and "limitOpen",
                pin #s as values
        debug (Boolean)
    Returns:
        Nothing
    """
    def __init__(self, sensors, debug=False):
        super(GarageDoorMonitor, self).__init__()
        self.bDebug = debug

        # determine sensor type
        self.enableSensors(sensors)

        # read limit switches to initialize states
        self.readLimitSwitches()

    """Enable sensors

    Sets up GPIO pins for all sensors

    Inputs:
        sensors - dict of sensors to enable
    Returns:
        Nothing, but does throw exception if it fails
    """
    def enableSensors(self, sensors):
        for sensor in sensors:
            if sensor in self.validSensorTypes:
                if sensors[sensor] is not None and sensors[sensor] != "":
                    self.sensorType[sensor] = True
                    self.pins[sensor] = int(sensors[sensor])
                    GPIO.setup(self.pins[sensor], GPIO.IN)
                    if self.bDebug:
                        s = "{}: pin {}".format(sensor, self.pins[sensor])
                        print "-d- gdMonitor: %s" % s
        return

    """Clean up GPIO

    Inputs:
        None
    Returns:
        Nothing
    """
    def cleanup(self):
        GPIO.cleanup()
        return

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
        return

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

    """Read limit switches

    Inputs:
        None
    Returns:
        Nothing
    """
    def readLimitSwitches(self):
        if self.sensorType["limitOpen"] or self.sensorType["limitClosed"]:
            if self.bDebug:
                print "-d- gdMonitor: reading limit swiches"
            self.limitStates["open"] = GPIO.input(self.pins["limitOpen"])
            self.limitStates["closed"] = GPIO.input(self.pins["limitClosed"])
            if self.bDebug:
                sOpen = "o{}".format(self.limitStates["open"])
                sClosed = "c{}".format(self.limitStates["closed"])
                print "-d- gdMonitor: Limit states: {}, {}".format(sOpen,
                                                                   sClosed)
        return

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

    """Determine state of garage door

    Inputs:
        None
    Returns:
        integer between 0-100 representing % door is open
    """
    def getDoorState(self):
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
                doorState = 0 if limitStates["closed"] else 100
        # only check rotary encoder if enabled and neither limit switch was ON
        if self.sensorType["rotary"] and not limitState:
            doorState = int(interp(self.rotaryCount,
                                   [self.rotaryLimits["closed"],
                                    self.rotaryLimits["open"]],
                                   [0, 100]
                                   )
                            )
        return doorState

    """Get current units - not relevant for garage door detector

    Inputs:
        None
    Returns:
        Nothing
    """
    def getUnits(self):
        return

    """Update sensor units

    Inputs:
        units - whatever you want, it's unused
    Returns:
        Nothing
    """
    def setUnits(self, units):
        return
