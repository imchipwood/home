import Adafruit_DHT
from sensor import *

class Humidity(Sensor):
    humidity = 0.0
    temperature = 0.0
    units = 'c'
    sensorType = { '11': Adafruit_DHT.DHT11,
                    '22': Adafruit_DHT.DHT22,
                    '2302': Adafruit_DHT.AM2302 }
    bDebug = False

    """ Initialize a Humidity sensor
        Inputs:
            sensor_type (Integer or String - which kind of DHT. See self.sensorType for valid options)
            pin number (Integer - GPIO pin)
            units (String - Celcius or Fahrenheit)
            debug (Boolean)
        Returns:
            Nothing
    """
    def __init__(self, sensor_type, pin, units, debug=False):
        super(Humidity, self).__init__()
        self.bDebug = debug
        # sensor type
        self.setSensorType(str(sensor_type))
        # pin
        self.pin = pin
        # units
        self.setUnits(units)

    """ Force Humidity sensor to update readings
        Inputs:
            None
        Returns:
            Nothing
    """
    def read(self):
        self.humidity = -999
        self.temperature = -999
        if self.state:
            hum, temp = Adafruit_DHT.read_retry(self.sensor_type, self.pin)
            if temp is not None:
                self.temperature = temp
            else:
                self.temperature = -999
            if hum is not None:
                self.humidity = hum

    """ Get last humidity reading
        Inputs:
            None
        Returns:
            Humidity in %
    """
    def getHumidity(self):
        return self.humidity

    """ Get last temperature reading
        Inputs:
            None
        Returns:
            Temperature in self.units
    """
    def getTemperature(self):
        if self.units.lower() == 'f':
            return self.temperature * 9.0/5.0 + 32.0
        else:
            return self.temperature

    """ Get current units
        Inputs:
            None
        Returns:
            Units as a single-char string
    """
    def getUnits(self):
        return self.units

    """ Update temperature units
        Inputs:
            units as a single char string, 'f' or 'c' (case-insensitive)
        Returns:
            Nothing, but does throw exception if it fails
    """
    def setUnits(self, units):
        if units.lower() in ['f', 'c']:
            self.units = units.lower()
        else:
            raise SensorException('Valid units: [c|f]\nYou entered: %s' % (units))

    """ Update sensor type
        Inputs:
            type as defined in self.sensorType
        Returns:
            Nothing, but does throw exception if it fails
    """
    def setSensorType(self, type):
        if type in self.sensorType:
            self.sensor_type = self.sensorType[type]
        else:
            raise SensorException('Valid sensor types: [11|22|2302]\nYou entered: %s' % (type))

