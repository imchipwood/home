"""
Simple wrapper around Adafruit's DHT module
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging
from typing import Tuple

from library.controllers import get_logger
from library.sensors import SensorBase

try:
    import Adafruit_DHT
except ImportError:  # pragma: no cover
    from . import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Couldn't import Adafruit_DHT - importing the mock module.")
    import library.mock.mock_Adafruit_DHT as Adafruit_DHT

from library.sensors import avg, SensorError


class EnvironmentSensor(SensorBase):
    """
    Basic wrapper around Adafruit's DHT module with support for
    setting temperature units (Celsius, Fahrenheit) and averaging
    multiple sensor reads.
    """
    VALID_TEMPERATURE_UNITS = ["celsius", "fahrenheit"]
    VALID_DHT_TYPES = {
        "11": Adafruit_DHT.DHT11,
        "22": Adafruit_DHT.DHT22,
        "2302": Adafruit_DHT.AM2302
    }

    def __init__(self, config, debug=False):
        """
        Constructor for EnvironmentSensor object
        @param config: configuration object for environment sensing
        @type config: library.config.environment.EnvironmentConfig
        @param debug: Flag to enable/disable debug prints
        @type debug: bool
        """
        super().__init__()

        self.config = config
        self.debug = debug

        self.logger = get_logger(__name__, debug, config.log)

        # Initialize values for readings
        self._temperature = -999.0
        self._humidity = -999.0
        self._pin = None
        self.pin = self.config.pin

        # Set the sensor type & pin #
        self._sensor_type = Adafruit_DHT.DHT11
        self.sensor_type = self.config.sensor_type

        self._units = "fahrenheit"
        self.units = self.config.units

    def reset_readings(self):
        """
        Reset the stored temperature/humidity values
        """
        self.humidity = -999.0
        self.temperature = -999.0

    def read(self) -> Tuple[float, float]:
        """
        Read sensor and store results
        @return: tuple of latest readings, humidity then temperature
        @rtype: tuple[float, float]
        """
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor_type, self.pin)
        if humidity is None or temperature is None:
            raise SensorError("Failed to read sensor!")  # pragma: no cover
        else:
            self.logger.debug(f"hum: {humidity:0.1f}, temp: {temperature:0.1f}")
        self.humidity = humidity
        self.temperature = temperature
        return humidity, temperature

    def read_n_times(self, num_reads=5) -> Tuple[float, float]:
        """
        Read the environment sensor n times and return the average
        Also sets the humidity/temperature class properties to the calculated
        average
        @param num_reads: number of times to read the sensor. Default: 5
        @type num_reads: int or float or str
        @return: tuple of averaged readings, humidity then temperature
        @rtype: tuple(float, float)
        """
        # Convert n to an int and ensure it's valid
        num_reads = int(num_reads)
        assert num_reads > 0, "n < 1! n needs to be larger than 0! Please try again!"

        # Set up lists for the number of desired readings
        temperature = [0.0] * num_reads
        humidity = [0.0] * num_reads

        # Everything is good - do the readings
        self.reset_readings()
        for i in range(num_reads):
            humidity[i], temperature[i] = self.read()

        self.humidity = avg(humidity)
        self.temperature = avg(temperature)
        self.logger.debug(f"Averages - hum: {avg(humidity):0.1f}, temp: {avg(temperature):0.1f}")

        return self.humidity, self.temperature

    @property
    def temperature(self) -> float:
        """
        @return: The most recent temperature reading in the desired units
        @rtype: float
        """
        return self.celsius if self.is_celsius() else self.fahrenheit

    @temperature.setter
    def temperature(self, temperature):
        """
        Set a new temperature
        @param temperature: new temperature in Celsius
        @type temperature: float or int or str
        """
        self._temperature = float(temperature) if temperature is not None else -999.0

    @property
    def humidity(self) -> float:
        """
        @return: The most recent humidity reading
        @rtype: float
        """
        return self._humidity

    @humidity.setter
    def humidity(self, humidity):
        """
        Set a new humidity
        @param humidity: new humidity
        @type humidity: float or int or str
        """
        self._humidity = float(humidity) if humidity is not None else -999.0

    def is_celsius(self) -> bool:
        """
        Check if we're set to Celsius
        @return: whether or not current units are set to celsius
        @rtype: bool
        """
        return self.units == "celsius"

    @property
    def fahrenheit(self) -> float:
        """
        Get the most recent temperature reading in Fahrenheit
        @return: temperature in Fahrenheit
        @rtype: float
        """
        return self._temperature * 9.0 / 5.0 + 32.0

    @property
    def celsius(self) -> float:
        """
        Get the most recent temperature reading in Celsius
        @return: temperature in Celsius
        @rtype: float
        """
        return self._temperature

    @property
    def pin(self) -> int:
        """
        Get pin number
        @rtype: int
        """
        return self._pin

    @pin.setter
    def pin(self, pin):
        """
        Set pin number
        @param pin: pin number
        @type pin: int
        """
        self._pin = pin
        self.logger.debug(f"Pin set to: {pin}")

    @property
    def units(self) -> str:
        """
        Get the current units
        @return: current units
        @rtype: str
        """
        return self._units

    @units.setter
    def units(self, units):
        """
        Change the current temperature units to Fahrenheit or Celsius
        @param units: new units as a single char string - 'f' or 'c' are valid
        @type units: str
        """
        EnvironmentSensor.validate_units(units)
        self._units = units.lower()
        self.logger.debug(f"Units set to: {self.units}")

    @property
    def sensor_type(self) -> int:
        """
        Get the current sensor type
        @return: current sensor type
        @rtype: int
        """
        return self._sensor_type

    @sensor_type.setter
    def sensor_type(self, sensor_type):
        """
        Change the current sensor type
        @param sensor_type:
        @type sensor_type: str or int
        """
        EnvironmentSensor.validate_sensor_type(sensor_type)
        self._sensor_type = self.VALID_DHT_TYPES[str(sensor_type)]
        self.logger.debug(f"Sensor type set to: {sensor_type}")

    @staticmethod
    def validate_units(units):
        """
        Check that the given units are valid - raises AssertionError if invalid
        @param units: desired new units
        @type units: str
        """
        assert units.lower() in EnvironmentSensor.VALID_TEMPERATURE_UNITS, \
            f"Invalid units! Valid units: {EnvironmentSensor.VALID_TEMPERATURE_UNITS}"

    @staticmethod
    def validate_sensor_type(sensor_type):
        """
        Check that the given sensor type is valid - raises AssertionError if invalid
        @param sensor_type: desired new sensor type
        @type sensor_type: str or int
        """
        assert str(sensor_type) in EnvironmentSensor.VALID_DHT_TYPES.keys(), \
            f"Invalid sensor type! Valid types: {EnvironmentSensor.VALID_DHT_TYPES.keys()}"
