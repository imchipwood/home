import logging
import Adafruit_DHT
from sensor import Sensor, SensorException


class SensorHumidity(Sensor):
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
		super(SensorHumidity, self).__init__()

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
		self._humidity = -999.0
		self._temperature = -999.0

	def read(self):
		"""
		Read sensor and store results
		"""
		self.resetReadings()
		if self.state:
			hum, temp = Adafruit_DHT.read_retry(self.sensorType, self.pin)
			if temp is not None:
				self._temperature = temp
			if hum is not None:
				self._humidity = hum

	@property
	def temperature(self):
		"""
		@return: The most recent temperature reading
		@rtype: float
		"""
		return self._temperature

	@property
	def humidity(self):
		"""
		@return: The most recent humidity reading
		@rtype: float
		"""
		return self._humidity

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
		SensorHumidity.ValidateUnits(units)
		self._units = units.lower()
		if self.debug:
			logging.debug("-d- SensorHumidity: units set to {}".format(self.units))

	@property
	def sensorType(self):
		return self._sensorType

	@sensorType.setter
	def sensorType(self, newSensorType):
		"""
		Change the current sensor type
		@param newSensorType:
		@type newSensorType: str or int
		"""
		SensorHumidity.ValidateSensorType(newSensorType)
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
		assert units.lower() in SensorHumidity.VALID_TEMPERATURE_UNITS, \
			"Invalid units! Valid units: {}".format(
				", ".join(SensorHumidity.VALID_TEMPERATURE_UNITS)
			)

	@staticmethod
	def ValidateSensorType(sensorType):
		"""
		Check that the given sensor type is valid - raises AssertionError if invalid
		@param sensorType: desired new sensor type
		@type sensorType: str or int
		"""
		assert str(sensorType) in SensorHumidity.VALID_DHT_TYPES.keys(), \
			"Invalid sensor type! Valid types: {}".format(
				", ".join(SensorHumidity.VALID_DHT_TYPES.keys())
			)
