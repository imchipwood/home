from library.sensors.environment import EnvironmentSensor
from library.sensors.camera import Camera

from library.config import ConfigurationHandler, SENSOR_CLASSES

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)


class TestEnvironmentSensor:
    sensor = EnvironmentSensor(
        config=CONFIGURATION_HANDLER.get_sensor_config("environment"),
        debug=True
    )
    def test_read(self):
        """
        Check that reading the sensor returns new values
        """
        self.sensor.reset_readings()
        self.sensor.units = "celsius"
        assert self.sensor.humidity == -999.0
        assert self.sensor.temperature == -999.0
        humidity, temperature = self.sensor.read()
        assert humidity != -999.0
        assert humidity == self.sensor.humidity
        assert temperature != -999.0
        assert temperature == self.sensor.temperature

    def test_units(self):
        """
        Check that the reading results match the desired units
        """
        self.sensor.reset_readings()
        self.sensor.units = 'celsius'
        humidity, temperature = self.sensor.read()
        fahrenheit = temperature * 9.0 / 5.0 + 32.0
        assert fahrenheit == self.sensor.fahrenheit
        assert temperature == self.sensor.temperature
        assert temperature == self.sensor.celsius

        # Change units
        self.sensor.units = 'fahrenheit'
        assert fahrenheit == self.sensor.temperature


# def test_CameraSensor_settings():
#     config = CONFIGURATION_HANDLER.get_sensor_config(SENSOR_CLASSES.CAMERA)
#     with Camera(config) as sensor:
#         assert sensor.brightness == 50
#         assert sensor.resolution == [3280, 2464]
