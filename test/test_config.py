from inspect import ismethod
import os
import json
import pytest

from library.config import ConfigurationHandler, SENSOR_CLASSES
from library.config.environment import EnvironmentConfig
from library.config.gpio_monitor import GPIOMonitorConfig
from library.config.camera import CameraConfig
from library.config.pushbullet import PushbulletConfig
from library.config.mqtt import MQTTConfig

from library.controllers.environment import EnvironmentController
from library.controllers.camera import PiCameraController
from library.controllers.gpio_monitor import GPIOMonitorController
from library.controllers.pushbullet import PushbulletController

# CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "pytest.json")
CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)

ALT_CONFIG_PATH = "pytest_nomqtt.json"
ALT_CONFIGURATION_HANDLER = ConfigurationHandler(ALT_CONFIG_PATH)


def teardown_module():
    for sensor in CONFIGURATION_HANDLER:
        sensor.cleanup()
    for sensor in ALT_CONFIGURATION_HANDLER:
        sensor.cleanup()


class Test_ConfigurationHandler:

    @pytest.mark.parametrize("target_type,expected_class", [
        (SENSOR_CLASSES.ENVIRONMENT, EnvironmentConfig),
        (SENSOR_CLASSES.GPIO_MONITOR, GPIOMonitorConfig),
        (SENSOR_CLASSES.CAMERA, CameraConfig),
        (SENSOR_CLASSES.PUSHBULLET, PushbulletConfig),
    ])
    def test_get_sensor_config(self, target_type, expected_class):
        """
        Test ConfigurationHandler gives expected config class
        for all supported types
        @param target_type: Target config type (environment, door_monitor, etc.)
        @type target_type: str
        @param expected_class: Expected object based on target_type
        @type expected_class: library.config.BaseConfiguration
        """
        for handler in [CONFIGURATION_HANDLER, ALT_CONFIGURATION_HANDLER]:
            config = handler.get_sensor_config(target_type)

            # Check the class is as expected
            assert isinstance(config, expected_class)
            assert config.mqtt_topic

    @pytest.mark.parametrize("target_type,expected_class", [
        (SENSOR_CLASSES.ENVIRONMENT, EnvironmentController),
        (SENSOR_CLASSES.CAMERA, PiCameraController),
        (SENSOR_CLASSES.GPIO_MONITOR, GPIOMonitorController),
        (SENSOR_CLASSES.PUSHBULLET, PushbulletController),
    ])
    def test_get_sensor_controller(self, target_type, expected_class):
        """
        Test ConfigurationHandler gives expected controller class
        for all supported types and that the controller has the required
        abstract methods defined
        @param target_type: Target config type (environment, door_monitor, etc.)
        @type target_type: str
        @param expected_class: Expected object based on target_type
        @type expected_class: library.controllers.BaseController
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(target_type, debug=True)

        # Check the class is as expected
        assert isinstance(controller, expected_class)

        # Check all the methods are defined
        assert ismethod(controller.start)
        assert ismethod(controller.stop)
        assert ismethod(controller.loop)
        assert ismethod(controller.cleanup)


class Test_MQTT:
    mqtt_path = "pytest_mqtt.json"
    sensor_path = "pytest_environment.json"

    def test_topics(self):
        """
        Test that the MQTTConfig has the expected topics
        """
        mqtt = MQTTConfig(self.mqtt_path, self.sensor_path)

        assert len(mqtt.topics) == 1

    def test_payload(self):
        """
        Test that the Topic can create the correct payload
        Also test that missing payload keys causes an exception
        """
        mqtt = MQTTConfig(self.mqtt_path, self.sensor_path)
        temperature = 123.45
        humidity = 67.89
        units = "Fahrenheit"
        expected_payload = {
            "temperature": str(temperature),
            "humidity": str(humidity),
            "units": units
        }
        topic = list(mqtt.topics.values())[0]

        payload = topic.payload(temperature=temperature, humidity=humidity, units=units)
        assert json.loads(payload) == expected_payload

        with pytest.raises(Exception, message="Expected exception for missing 'units' key"):
            topic.payload(temperature=temperature, humidity=humidity)
