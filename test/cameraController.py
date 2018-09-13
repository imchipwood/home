import os
import time

from lib.sensors.cameraController import PiCameraController
from lib.services.pushbulletNotify import PushbulletImageNotify


def test():
	# config path
	configFileName = 'garageDoor.txt'
	configFilePath = os.path.join(os.path.dirname(__file__), '..', 'conf', configFileName)

	print("Loading config file {}".format(configFilePath))
	camera = PiCameraController(configFile=configFilePath, debug=True)
	print("Capturing image: {}".format(camera.cameraFile))
	camera.capture()

	
if __name__ == '__main__':
	test()
