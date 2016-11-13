import Adafruit_DHT
from sensor import Sensor, SensorException


class GarageDoorDetector(Sensor):
    """Garage Door Detector Class

    This class houses all functions required monitor the state
    of a garage door.

    Types of sensors to support:
    1. Rotary Encoder (attached to motor, detect rotations)
    2. Limit switch(es) - top and bottom to detect only fully open and closed
    """
    # bogus sensor types for now
    validSensorTypes = {
        "rotary": "rotary",
        "limit": "limit"
    }
    sensorType = {
        "rotary": False,
        "limit": False
    }
    pins = {
        "rotary": "",
        "limit": {}
    }
    bDebug = False

    """Initialize a Humidity sensor

    Inputs:
        sensor_type (Integer or String - which kind of DHT sensor.)
        pin number (Integer - GPIO pin)
        units (String - Celcius or Fahrenheit)
        debug (Boolean)
    Returns:
        Nothing
    """
    def __init__(self, sensorTypes, pins, debug=False):
        super(GarageDoorDetector, self).__init__()
        self.bDebug = debug
        # determine sensor type
        self.setSensorType(sensorTypes)
        # based on sensor type, set pins
        if self.sensorType["rotary"]:
            self.pins["rotary"] = int(pins)
        if self.sensorType["limit"]:
            self.pins["limit"]["low"] = pins['low']
            self.pins["limit"]["high"] = pins['high']

    """Take readings based on sensorType

    Inputs:
        None
    Returns:
        Nothing
    """
    def read(self):
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
        dict with 'low' and 'high' keys representing state of limit switches
    """
    def readLimitSwitches(self):
        # read pins["limit"]["low"] and pins["limit"]["high"]
        return

    """Get current units - not relevant for garage door detector

    Inputs:
        None
    Returns:
        None
    """
    def getUnits(self):
        return

    """Update temperature units

    Inputs:
        units - whatever you want, it's unused
    Returns:
        None
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
                    sType = "sensorType: %s=%s" % (sensorType, self.sensorType)
                    print "-d- SensorGarageDoorDetector: %s" % (sType)
            else:
                sException = "Valid sensor types: ["
                sException += "|".join(self.validSensorTypes.keys()) + "]"
                raise SensorException(sException)
