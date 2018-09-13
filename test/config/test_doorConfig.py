import os

from definitions import CONFIG_DIR
from library.config.doorConfig import DoorConfig


def test_DoorConfig():
	configPath = os.path.join(CONFIG_DIR, "doorSettings.json")
	config = DoorConfig(configPath)

	assert config.gpio.get('pin_control', -10) == 17
	assert config.gpio.get('pin_sensor', -10) == 4

	assert config.mqtt.client == 'garageDoor'
