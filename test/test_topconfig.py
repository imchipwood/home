from inspect import ismethod
import pytest

from library.config import ConfigurationHandler
from library.config.environment import EnvironmentConfig
from library.config.door_monitor import DoorMonitorConfig

from library.controllers.environment import EnvironmentController

CONFIG_PATH = "test.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)


@pytest.mark.parametrize("target_type,expected_class", [
    ("environment", EnvironmentConfig),
    ("door_monitor", DoorMonitorConfig),
])
def test_get_sensor_config(target_type, expected_class):
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
])
def test_get_sensor_controller(target_type, expected_class):
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
