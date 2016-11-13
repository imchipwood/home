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
    validSensorTypes = ["rotary", "limit"]
    sensorType = {
        "rotary": False,
        "limit": False
    }
    pins = {
        "rotary": "",
        "limit": {}
    }
    limitStates = {
        "low": False,
        "high": False
    }
    rotaryCount = 0
    rotaryLimits = {
        "closed": 0,
        "open": 100
    }
    bDebug = False

    """Initialize a Humidity sensor

    Inputs:
        sensor_type (Integer or String - which kind of DHT sensor.)
        pins - dict with keys "rotary", "limitClosed", and "limitOpen"
        units (String - Celcius or Fahrenheit)
        debug (Boolean)
    Returns:
        Nothing
    """
    def __init__(self, sensorTypes, pins, debug=False):
        super(GarageDoorMonitor, self).__init__()
        self.bDebug = debug

        # determine sensor type
        self.setSensorType(sensorTypes)

        # initialize all GPIO
        self.initGPIO(pins)

        # read limit switches to initialize states
        self.readLimitSwitches()

    """Initialize GPIO

    Inputs:
        None
    Returns:
        Nothing
    """
    def initGPIO(self, pins):
        GPIO.setmode(GPIO.BCM)
        if self.sensorType["rotary"]:
            self.pins["rotary"] = int(pins["rotary"])
        if self.sensorType["limit"]:
            self.pins["limit"]["closed"] = pins["limitClosed"]
            self.pins["limit"]["open"] = pins["limitOpen"]

            GPIO.setup(self.pins["limit"]["closed"], GPIO.IN)
            GPIO.setup(self.pins["limit"]["open"], GPIO.IN)
        return

    """Clean up GPIO

    Inputs:
        None
    Returns:
        Nothing
    """
    def cleanup(self):
        GPIO.cleanup()

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
        if sensorType["limit"]:
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
        self.limitStates["closed"] = GPIO.input(self.pins["limit"]["closed"])
        self.limitStates["open"] = GPIO.input(self.pins["limit"]["open"])
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
            if self.limitStates["closed"] and self.limitStates["open"]:
                return -999
            elif self.limitStates["closed"] or self.limitStates["open"]:
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
            if self.limitStates["closed"] and self.limitStates["open"]:
                return False
            elif self.limitStates["closed"]:
                # rotaryLimits["closed"] = rotaryCount
                rotaryCount = 0
            elif self.limitStates["open"]:
                rotaryLimits["open"] = rotaryCount
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
    def setSensorType(self, sensorTypes):
        for sensorType in sensorTypes:
            if sensorType in self.validSensorTypes:
                self.sensorType[sensorType] = True
                if self.bDebug:
                    sType = "sensorType: %s" % (sensorType)
                    print "-d- SensorGarageDoorDetector: Enablign %s" % (sType)
            else:
                sException = "Valid sensor types: ["
                sException += "|".join(self.validSensorTypes) + "]"
                raise SensorException(sException)
