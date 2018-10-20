from library.sensors.sensor_environment import EnvironmentSensor

global env_sensor
env_sensor = None
""" @type: EnvironmentSensor """


def setup_module():
    global env_sensor
    env_sensor = EnvironmentSensor(
        sensor_type='22',
        pin=4,
        units='celsius',
        debug=True
    )


class TestEnvironmentSensor:
    def test_read(self):
        """
        Check that reading the sensor returns new values
        """
        env_sensor.reset_readings()
        assert env_sensor.humidity == -999.0
        assert env_sensor.temperature == -999.0
        humidity, temperature = env_sensor.read()
        assert humidity != -999.0
        assert humidity == env_sensor.humidity
        assert temperature != -999.0
        assert temperature == env_sensor.temperature

    def test_units(self):
        """
        Check that the reading results match the desired units
        """
        env_sensor.reset_readings()
        env_sensor.units = 'celsius'
        humidity, temperature = env_sensor.read()
        fahrenheit = temperature * 9.0 / 5.0 + 32.0
        assert fahrenheit == env_sensor.fahrenheit
        assert temperature == env_sensor.temperature
        assert temperature == env_sensor.celsius

        # Change units
        env_sensor.units = 'fahrenheit'
        assert fahrenheit == env_sensor.temperature
