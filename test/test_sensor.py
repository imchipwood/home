from library.sensors.environment import EnvironmentSensor
from library.sensors.gpio_monitor import GPIO_Monitor, GPIO
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


class TestGPIOMonitorSensor:
    def test_sensor(self):
        sensor = GPIO_Monitor(
            config=CONFIGURATION_HANDLER.get_sensor_config(SENSOR_CLASSES.GPIO_MONITOR),
            debug=True
        )
        assert sensor.pull_up_down in [GPIO.PUD_UP, GPIO.PUD_DOWN]
        sensor.read()
        sensor.cleanup()


class TestCamera:
    def test_sensor(self):
        config = CONFIGURATION_HANDLER.get_sensor_config(SENSOR_CLASSES.CAMERA)
        with Camera(config, debug=True) as sensor:
            assert sensor.capture_delay >= 0
            assert len(sensor.resolution) == 2
            assert sensor.iso

            sensor.capture()
