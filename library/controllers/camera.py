"""
Camera Controller
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging
import time
import os

try:
    from picamera import PiCamera
except:
    logging.warning("Failed to import picamera - using mock")
    from library.mock.mock_picamera import PiCamera

from library.controllers import BaseController
from library.communication.mqtt import MQTTClient
from library.config.cameraConfig import CameraConfig


class PiCameraController(PiCamera, BaseController):
    def __init__(self, config, debug=False):
        super(PiCameraController, self).__init__(config=config, debug=debug)

        # Set up the camera

