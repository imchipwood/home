from library.config import ConfigurationHandler, SENSORCLASSES
from library.config.camera import CameraConfig
from library.config.environment import EnvironmentConfig
from library.config.gpio_monitor import GPIOMonitorConfig
from library.config.gpio_driver import GPIODriverConfig, ConfigKeys
from library.sensors.camera import Camera
from library.sensors.environment import EnvironmentSensor
from library.sensors.gpio_monitor import GPIOMonitor, GPIO
from library.sensors.gpio_driver import GPIODriver

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH, debug=True)

MOCK_GPIO_STATE = None


def mock_gpio_write(direction):
    global MOCK_GPIO_STATE
    MOCK_GPIO_STATE = direction


class TestEnvironmentSensor:
    config = CONFIGURATION_HANDLER.get_sensor_config("environment")  # type: EnvironmentConfig
    sensor = EnvironmentSensor(
        config=config,
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

    def test_read_n_times(self):
        """
        Check that reading n times returns new values
        """
        self.sensor.reset_readings()
        self.sensor.units = "celsius"
        humidity, temperature = self.sensor.read_n_times(5)
        assert humidity != -999
        assert temperature != -999

    def test_units(self):
        """
        Check that the reading results match the desired units
        """
        self.sensor.reset_readings()
        self.sensor.units = "celsius"
        humidity, temperature = self.sensor.read()
        fahrenheit = temperature * 9.0 / 5.0 + 32.0
        assert fahrenheit == self.sensor.fahrenheit
        assert temperature == self.sensor.temperature
        assert temperature == self.sensor.celsius

        # Change units
        self.sensor.units = "fahrenheit"
        assert fahrenheit == self.sensor.temperature


class TestGPIOMonitorSensor:
    
    def test_sensor(self):
        config = CONFIGURATION_HANDLER.get_sensor_config(SENSORCLASSES.GPIO_MONITOR)  # type: GPIOMonitorConfig
        sensor = GPIOMonitor(
            config=config
        )
        assert sensor.pull_up_down in [GPIO.PUD_UP, GPIO.PUD_DOWN]
        sensor.read()
        sensor.cleanup()


class TestGPIODriverSensor:

    def test_sensor_write(self, monkeypatch):
        global MOCK_GPIO_STATE
        config = CONFIGURATION_HANDLER.get_sensor_config(SENSORCLASSES.GPIO_DRIVER)  # type: GPIODriverConfig
        sensor = GPIODriver(config=config)
        monkeypatch.setattr(sensor, "write", mock_gpio_write)

        assert sensor.pin == 17

        sensor.write(GPIO.HIGH)
        assert MOCK_GPIO_STATE == GPIO.HIGH

        sensor.write(GPIO.LOW)
        assert MOCK_GPIO_STATE == GPIO.LOW

        sensor.cleanup()

    def test_sensor_active_direction(self, monkeypatch):
        global MOCK_GPIO_STATE
        config = CONFIGURATION_HANDLER.get_sensor_config(SENSORCLASSES.GPIO_DRIVER)  # type: GPIODriverConfig
        sensor = GPIODriver(config=config)
        monkeypatch.setattr(sensor, "write", mock_gpio_write)

        sensor.config.config[ConfigKeys.ACTIVE_DIRECTION] = "HIGH"
        sensor.write_on()
        assert MOCK_GPIO_STATE == GPIO.HIGH
        sensor.write_off()
        assert MOCK_GPIO_STATE == GPIO.LOW

        sensor.config.config[ConfigKeys.ACTIVE_DIRECTION] = "LOW"
        sensor.write_on()
        assert MOCK_GPIO_STATE == GPIO.LOW
        sensor.write_off()
        assert MOCK_GPIO_STATE == GPIO.HIGH

        sensor.cleanup()


class TestCamera:
    def test_sensor(self):
        config = CONFIGURATION_HANDLER.get_sensor_config(SENSORCLASSES.CAMERA)  # type: CameraConfig
        with Camera(config, debug=True) as sensor:
            assert sensor.capture_delay >= 0
            assert len(sensor.resolution) == 2
            assert sensor.iso

            sensor.capture()
