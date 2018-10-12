import logging

try:
	import Adafruit_DHT
except:
	logging.warn("Couldn't import Adafruit_DHT - assuming this machine is not a Raspberry Pi and importing the mock module.")
	import library.sensors.Adafruit_DHT_mock as Adafruit_DHT

from library.sensors.sensor import Sensor
from library.sensors import avg


class EnvironmentSensor(Sensor):
	VALID_TEMPERATURE_UNITS = ["celsius", "fahrenheit"]
	VALID_DHT_TYPES = {
		"11": Adafruit_DHT.DHT11,
		"22": Adafruit_DHT.DHT22,
		"2302": Adafruit_DHT.AM2302
	}

	def __init__(self, sensorType, pin, units="fahrenheit", debug=False):
		"""
		Constructor for SensorHumidity object
		@param sensorType: Desired Adafruit DHT sensor type
		@type sensorType: int or str
		@param pin: GPIO pin for reading sensor
		@type pin: int or str
		@param units: Desired temperature units. Fahrenheit or Celsius
		@type units: str
		@param debug: Flag to enable/disable debug prints
		@type debug: bool
		"""
		super(EnvironmentSensor, self).__init__()

		self.debug = debug

		# Initialize values for readings
		self._temperature = -999.0
		self._humidity = -999.0

		# Set the sensor type & pin #
		self._sensorType = Adafruit_DHT.DHT11
		self.sensorType = sensorType
		self.pin = pin

		self._units = "fahrenheit"
		self.units = units

	def resetReadings(self):
		"""
		Reset the stored temperature/humidity values
		"""
		self._humidity = -999.0
		self._temperature = -999.0

	def read(self):
		"""
		Read sensor and store results
		@return: tuple of latest readings, temperature then humidity
		@rtype: tuple[float, float]
		"""
		if not self.state:
			self.resetReadings()
			logging.warn("Sensor is disabled - will not read as requested!")
			return None, None

		self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensorType, self.pin)
		return self.temperature, self.humidity

	def readntimes(self, n=5):
		"""
		Read the environment sensor n times and return the average
		@param n: number of times to read the sensor. Default: 5
		@type n: int or float or str
		@return: tuple of averaged readings
		@rtype: tuple(float, float)
		"""
		# Convert n to an int and ensure it's valid
		n = int(n)
		assert n > 0, "n < 1! n needs to be larger than 0! Please try again!"

		# Set up lists for the number of desired readings
		temperature = [0.0] * n
		humidity = [0.0] * n

		# Check that we're enabled
		if not self.state:
			logging.warn("Sensor is disabled - will not read it {} times as requested!".format(n))
			return None, None

		# Everything is good - do the readings
		self.resetReadings()
		for i in range(n):
			temperature[i], humidity[i] = self.read()

		self.temperature = avg(temperature)
		self.humidity = avg(humidity)

		return self.temperature, self.humidity

	@property
	def temperature(self):
		"""
		@return: The most recent temperature reading in the desired units
		@rtype: float
		"""
		return self.celsius if self.isCelsius() else self.fahrenheit

	@temperature.setter
	def temperature(self, temperature):
		"""
		Set a new temperature
		@param temperature: new temperature
		@type temperature: float or int or str
		"""
		self._temperature = float(temperature) if temperature is not None else -999.0

	@property
	def humidity(self):
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

	def isCelsius(self):
		"""
		Check if we're set to Celsius
		@return: whether or not current units are set to celsius
		@rtype: bool
		"""
		return self.units == 'celsius'

	@property
	def fahrenheit(self):
		"""
		Get the most recent temperature reading in Fahrenheit
		@return: temperature in Fahrenheit
		@rtype: float
		"""
		return self._temperature * 9.0 / 5.0 + 32.0

	@property
	def celsius(self):
		"""
		Get the most recent temperature reading in Celsius
		@return: temperature in Celsius
		@rtype: float
		"""
		return self._temperature

	@property
	def units(self):
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
		EnvironmentSensor.ValidateUnits(units)
		self._units = units.lower()
		if self.debug:
			logging.debug("-d- SensorHumidity: units set to {}".format(self.units))

	@property
	def sensorType(self):
		"""
		Get the current sensor type
		@return: current sensor type
		@rtype: int
		"""
		return self._sensorType

	@sensorType.setter
	def sensorType(self, newSensorType):
		"""
		Change the current sensor type
		@param newSensorType:
		@type newSensorType: str or int
		"""
		EnvironmentSensor.ValidateSensorType(newSensorType)
		self._sensorType = self.VALID_DHT_TYPES[str(newSensorType)]
		if self.debug:
			logging.debug("-d- SensorHumidity type: {}".format(newSensorType))

	@staticmethod
	def ValidateUnits(units):
		"""
		Check that the given units are valid - raises AssertionError if invalid
		@param units: desired new units
		@type units: str
		"""
		assert units.lower() in EnvironmentSensor.VALID_TEMPERATURE_UNITS, \
			"Invalid units! Valid units: {}".format(
				", ".join(EnvironmentSensor.VALID_TEMPERATURE_UNITS)
			)

	@staticmethod
	def ValidateSensorType(sensorType):
		"""
		Check that the given sensor type is valid - raises AssertionError if invalid
		@param sensorType: desired new sensor type
		@type sensorType: str or int
		"""
		assert str(sensorType) in EnvironmentSensor.VALID_DHT_TYPES.keys(), \
			"Invalid sensor type! Valid types: {}".format(
				", ".join(EnvironmentSensor.VALID_DHT_TYPES.keys())
			)
