from inspect import ismethod
import json
import pytest

from library.config import ConfigurationHandler
from library.config.environment import EnvironmentConfig
from library.config.gpio_monitor import GPIOMonitorConfig
from library.config.camera import CameraConfig
from library.config.mqtt import MQTTConfig

from library.controllers.environment import EnvironmentController
from library.controllers.camera import PiCameraController
from library.controllers.gpio_monitor import GPIOMonitorController

CONFIG_PATH = "test.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)


class Test_ConfigurationHandler:
    @pytest.mark.parametrize("target_type,expected_class", [
        ("environment", EnvironmentConfig),
        ("gpio_monitor", GPIOMonitorConfig),
        ("camera", CameraConfig),
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
        config = CONFIGURATION_HANDLER.get_sensor_config(target_type)

        # Check the class is as expected
        assert isinstance(config, expected_class)

    @pytest.mark.parametrize("target_type,expected_class", [
        ("environment", EnvironmentController),
        ("camera", PiCameraController),
        ("gpio_monitor", GPIOMonitorController),
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
        controller = CONFIGURATION_HANDLER.get_sensor_controller(target_type)

        # Check the class is as expected
        assert isinstance(controller, expected_class)

        # Check all the methods are defined
        assert ismethod(controller.start)
        assert ismethod(controller.stop)
        assert ismethod(controller.loop)
        assert ismethod(controller.cleanup)


class Test_MQTT:
    mqtt_path = "test_mqtt.json"
    sensor_path = "test_environment.json"
    expected_topic_name = "home-assistant/test/sub"

    def test_topics(self):
        """
        Test that the MQTTConfig has the expected topics
        """
        mqtt = MQTTConfig(self.mqtt_path, self.sensor_path)

        assert len(mqtt.topics) == 1

        assert self.expected_topic_name in mqtt.topics
        assert self.expected_topic_name in mqtt.topics_publish

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
        topic = mqtt.topics_publish.get(self.expected_topic_name)

        payload = topic.payload(temperature=temperature, humidity=humidity, units=units)
        assert json.loads(payload) == expected_payload

        with pytest.raises(Exception, message="Expected exception for missing 'units' key"):
            topic.payload(temperature=temperature, humidity=humidity)
