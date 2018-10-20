import logging

try:
	import Adafruit_DHT
except:
	logging.warning("Couldn't import Adafruit_DHT - assuming this machine is not a Raspberry Pi and importing the mock module.")
	import library.mock.mock_Adafruit_DHT as Adafruit_DHT

from library.sensors import avg


class EnvironmentSensor(object):
	VALID_TEMPERATURE_UNITS = ["celsius", "fahrenheit"]
	VALID_DHT_TYPES = {
		"11": Adafruit_DHT.DHT11,
		"22": Adafruit_DHT.DHT22,
		"2302": Adafruit_DHT.AM2302
	}

	def __init__(self, sensor_type, pin, units="fahrenheit", debug=False):
		"""
		Constructor for SensorHumidity object
		@param sensor_type: Desired Adafruit DHT sensor type
		@type sensor_type: int or str
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
		self.temperature = -999.0
		self._humidity = -999.0
		self.humidity = -999.0

		# Set the sensor type & pin #
		self._sensor_type = Adafruit_DHT.DHT11
		self.sensor_type = sensor_type
		self.pin = pin

		self._units = "fahrenheit"
		self.units = units

	def reset_readings(self):
		"""
		Reset the stored temperature/humidity values
		"""
		self.humidity = -999.0
		self.temperature = -999.0

	def read(self):
		"""
		Read sensor and store results
		@return: tuple of latest readings, humidity then temperature
		@rtype: tuple[float, float]
		"""
		humidity, temperature = Adafruit_DHT.read_retry(self.sensor_type, self.pin)
		self.humidity = humidity
		self.temperature = temperature
		return humidity, temperature

	def read_n_times(self, n=5):
		"""
		Read the environment sensor n times and return the average
		Also sets the humidity/temperature class properties to the calculated
		average
		@param n: number of times to read the sensor. Default: 5
		@type n: int or float or str
		@return: tuple of averaged readings, humidity then temperature
		@rtype: tuple(float, float)
		"""
		# Convert n to an int and ensure it's valid
		n = int(n)
		assert n > 0, "n < 1! n needs to be larger than 0! Please try again!"

		# Set up lists for the number of desired readings
		temperature = [0.0] * n
		humidity = [0.0] * n

		# Everything is good - do the readings
		self.reset_readings()
		for i in range(n):
			humidity[i], temperature[i] = self.read()
			logging.debug("{} - hum: {:0.1f}, temp: {:0.1f}".format(i, humidity[i], temperature[i]))

		self.humidity = avg(humidity)
		self.temperature = avg(temperature)
		logging.debug("Averages - hum: {:0.1f}, temp: {:0.1f}".format(humidity[i], temperature[i]))

		return self.humidity, self.temperature

	@property
	def temperature(self):
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

	def is_celsius(self):
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
		EnvironmentSensor.validate_units(units)
		self._units = units.lower()
		if self.debug:
			logging.debug("-d- SensorHumidity: units set to {}".format(self.units))

	@property
	def sensor_type(self):
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
		if self.debug:
			logging.debug("-d- SensorHumidity type: {}".format(sensor_type))

	@staticmethod
	def validate_units(units):
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
	def validate_sensor_type(sensor_type):
		"""
		Check that the given sensor type is valid - raises AssertionError if invalid
		@param sensor_type: desired new sensor type
		@type sensor_type: str or int
		"""
		assert str(sensor_type) in EnvironmentSensor.VALID_DHT_TYPES.keys(), \
			"Invalid sensor type! Valid types: {}".format(
				", ".join(EnvironmentSensor.VALID_DHT_TYPES.keys())
			)
