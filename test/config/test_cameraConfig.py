import os

from lib.config.cameraConfig import CameraConfig
from definitions import CONFIG_DIR


def test_CameraConfig():
	configPath = os.path.join(CONFIG_DIR, "cameraSettings.json")
	config = CameraConfig(configPath)

	assert config.brightness == 50
	assert config.rotation == 180
	assert config.iso in [200, 800]
	assert config.captureDelay == 10
