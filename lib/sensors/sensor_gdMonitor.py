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
        "low": False,
        "high": False
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
        self.setSensorType(sensors)

        # initialize all GPIO
        self.initGPIO(sensors)

        # read limit switches to initialize states
        self.readLimitSwitches()

    """Initialize GPIO

    Inputs:
        None
    Returns:
        Nothing
    """
    def initGPIO(self, sensors):
        GPIO.setmode(GPIO.BCM)
        for sensor in sensors:
            print "-d- {}, {}".format(sensor, sensors[sensor])
            if sensors[sensor] is not None:
                self.pins[sensor] = sensors[sensor]
                if self.bDebug:
                    print "-d- gdMonitor: pin {}: {}".format(sensor,
                                                             self.pins[sensor])
                    GPIO.setup(self.pins[sensor], GPIO.IN)
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
        if sensorType["rotary"]:
            self.readRotaryEncoder()
        if sensorType["limitOpen"] or sensorType["limitClosed"]:
            self.readLimitSwitches()
            self.updateRotaryCalibration()
        return

    """Read Rotary Encoder

    Inputs:
        None
    Returns:
        integer between 0-100 representing % door is open
    """
    def readRotaryEncoder(self):
        # read pins["rotary"]
        return

    """Read limit switches

    Inputs:
        None
    Returns:
        Nothing
    """
    def readLimitSwitches(self):
        self.limitStates["open"] = GPIO.input(self.pins["limitOpen"])
        self.limitStates["closed"] = GPIO.input(self.pins["limitClosed"])
        if self.bDebug:
            sOpen = "o{}".format(self.limitStates["open"])
            sClosed = "c{}".format(self.limitStates["closed"])
            print "-d- gdMonitor: Limit states: {}, {}".format(sOpen, sClosed)
        return

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
        if self.sensorType["limit"]:
            # check for error state
            if self.limitStates["open"] and self.limitStates["closed"]:
                return -999
            elif self.limitStates["open"] or self.limitStates["closed"]:
                limitState = True
                doorState = 0 if limitStates["closed"] else 100
        # only check rotary encoder if enabled and neither limit switch was ON
        if self.sensorType["rotary"] and not limitState:
            doorState = int(interp(rotaryCount,
                                   [rotaryLimits["closed"],
                                    rotaryLimits["open"]],
                                   [0, 100]
                                   )
                            )
        return doorState

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
        if sensorType["rotary"]:
            if self.limitStates["open"] and self.limitStates["closed"]:
                return False
            elif self.limitStates["open"]:
                rotaryLimits["open"] = rotaryCount
            elif self.limitStates["closed"]:
                rotaryCount = 0
        return True

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

    """Set sensor type

    Inputs:
        sensorTypes - array of sensorTypes to enable
    Returns:
        Nothing, but does throw exception if it fails
    """
    def setSensorType(self, sensors):
        for sensor in sensors:
            if sensors[sensor] is not None and sensors[sensor] != "":
                self.sensorType[sensor] = True
                if self.bDebug:
                    print "-d- gdMonitor: Enabling %s" % (sensor)
            else:
                sException = "Valid sensor types: ["
                sException += "|".join(self.validSensorTypes) + "]"
                raise SensorException(sException)
        return