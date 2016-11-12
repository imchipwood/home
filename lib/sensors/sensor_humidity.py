import Adafruit_DHT
from sensor import Sensor, SensorException


class SensorHumidity(Sensor):
    """Humidity Sensor Class

    This class houses all functions required to set up
    and take readings from a DHT humidity sensor
    """
    humidity = 0.0
    temperature = 0.0
    validUnits = ['c', 'f']
    validSensorTypes = {'11': Adafruit_DHT.DHT11,
                        '22': Adafruit_DHT.DHT22,
                        '2302': Adafruit_DHT.AM2302
                        }
    sensorType = validSensorTypes.values()[0]
    units = validUnits[0]
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
    def __init__(self, sensor_type, pin, units, debug=False):
        super(SensorHumidity, self).__init__()
        self.bDebug = debug
        # sensor type
        self.setSensorType(str(sensor_type))
        # pin
        self.pin = pin
        # units
        self.setUnits(units)

    """Take readings

    Inputs:
        None
    Returns:
        Nothing
    """
    def read(self):
        self.humidity = -999
        self.temperature = -999
        if self.state:
            hum, temp = Adafruit_DHT.read_retry(self.getSensorType(), self.pin)
            if temp is not None:
                self.temperature = temp
            else:
                self.temperature = -999
            if hum is not None:
                self.humidity = hum

    """Get last Humidity reading

    Inputs:
        None
    Returns:
        Humidity in %
    """
    def getHumidity(self):
        return self.humidity

    """Get last temperature reading

    Inputs:
        None
    Returns:
        Temperature in self.units
    """
    def getTemperature(self):
        if self.getUnits().lower() == 'f':
            return self.temperature * 9.0/5.0 + 32.0
        else:
            return self.temperature

    """Get current units

    Inputs:
        None
    Returns:
        Units as a single-char string
    """
    def getUnits(self):
        return self.units

    """Update temperature units

    Inputs:
        units as a single char string, 'f' or 'c' (case-insensitive)
    Returns:
        Nothing, but does throw exception if it fails
    """
    def setUnits(self, units):
        if units.lower() in self.validUnits:
            self.units = units.lower()
            if self.bDebug:
                print "-d- SensorHumidity: units set to %s" % (self.getUnits())
        else:
            sException = "Valid units: [" + "|".join(self.validUnits) + "]"
            raise SensorException(sException)

    """Get sensor type

    Inputs:
        None
    Returns:
        self.sensorType as defined in Adafruit_DHT class
    """
    def getSensorType(self):
        return self.sensorType

    """Set sensor type

    Inputs:
        type as defined in self.sensorType
    Returns:
        Nothing, but does throw exception if it fails
    """
    def setSensorType(self, sensor_type):
        if sensor_type in self.validSensorTypes:
            self.sensorType = self.validSensorTypes[sensor_type]
            if self.bDebug:
                sType = "sensorType: %s=%s" % (sensor_type, self.sensorType)
                print "-d- SensorHumidity: %s" % (sType)
        else:
            sException = "Valid sensor types: ["
            sException += "|".join(self.sensorType.keys()) + "]"
            raise SensorException(sException)
