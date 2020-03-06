import json
from inspect import ismethod
import os

import pytest

from library import TEST_CONFIG_DIR
from library.config import ConfigurationHandler, SENSORCLASSES, BaseConfiguration
from library.config.camera import CameraConfig
from library.config.environment import EnvironmentConfig
from library.config.gpio_monitor import GPIOMonitorConfig
from library.config.mqtt import MQTTConfig
from library.config.pushbullet import PushbulletConfig
from library.controllers.camera import PiCameraController
from library.controllers.environment import EnvironmentController
from library.controllers.gpio_monitor import GPIOMonitorController
from library.controllers.pushbullet import PushBulletController

# CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "pytest.json")
CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH, debug=True)

ALT_CONFIG_PATH = "pytest_nomqtt.json"
ALT_CONFIGURATION_HANDLER = ConfigurationHandler(ALT_CONFIG_PATH, debug=True)


def teardown_module():
    for sensor in CONFIGURATION_HANDLER:
        sensor.cleanup()
    for sensor in ALT_CONFIGURATION_HANDLER:
        sensor.cleanup()


class TestConfigurationHandler:

    def test_normalize_config_path(self):
        """
        Test that normalize_config_path properly changes base directory
        """
        first_config = "pytest.json"
        second_config = os.path.join(TEST_CONFIG_DIR, "inner_config", "pytest2.json")
        BaseConfiguration.normalize_config_path(first_config)
        assert BaseConfiguration.BASE_CONFIG_DIR == TEST_CONFIG_DIR
        BaseConfiguration.normalize_config_path(second_config)
        assert BaseConfiguration.BASE_CONFIG_DIR == os.path.join(TEST_CONFIG_DIR, "inner_config")

    @pytest.mark.parametrize("target_type,expected_class", [
        (SENSORCLASSES.ENVIRONMENT, EnvironmentConfig),
        (SENSORCLASSES.GPIO_MONITOR, GPIOMonitorConfig),
        (SENSORCLASSES.CAMERA, CameraConfig),
        (SENSORCLASSES.PUSHBULLET, PushbulletConfig),
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
            assert config.__class__ == expected_class
            assert hasattr(config, "mqtt_topic")

    @pytest.mark.parametrize("target_type,expected_class", [
        (SENSORCLASSES.ENVIRONMENT, EnvironmentController),
        (SENSORCLASSES.CAMERA, PiCameraController),
        (SENSORCLASSES.GPIO_MONITOR, GPIOMonitorController),
        (SENSORCLASSES.PUSHBULLET, PushBulletController),
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
        assert controller.__class__ == expected_class

        # Check all the methods are defined
        assert ismethod(controller.start)
        assert ismethod(controller.stop)
        assert ismethod(controller.loop)
        assert ismethod(controller.cleanup)


class TestMQTT:
    mqtt_path = "pytest_mqtt.json"
    sensor_path = "pytest_environment.json"

    def test_topics(self):
        """
        Test that the MQTTConfig has the expected topics
        """
        mqtt = MQTTConfig(self.mqtt_path, self.sensor_path)

        assert len(mqtt.topics) == 1

    def test_topics_deep(self):
        """
        Test that topics act as expected
        """
        config_path = "mqtt_config_test.json"
        config = MQTTConfig(self.mqtt_path, config_path)
        assert config.client_id == "mqtt_config_test"
        assert config.topics

        assert config.topics_subscribe
        subscribe = config.topics_subscribe["topic1"]
        assert subscribe.raw_payload == {"state": "Open"}
        assert subscribe.payload(state="Open") == {"state": "Open"}

        assert config.topics_publish
        both = config.topics_publish["topic2"]
        expected = {"capture": True, "delay": 5}
        received = json.loads(both.payload(capture=True, delay=5))
        assert received == expected

        publish = config.topics_publish["topic3"]
        assert publish.raw_payload == {"state": "publish"}
        assert publish.payload(state="publish") == json.dumps({"state": "publish"})

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
