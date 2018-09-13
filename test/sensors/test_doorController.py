import os

from definitions import CONFIG_DIR
from library.sensors.doorController import DoorController


class DoorControllerTest(object):
	def __init__(self):
		doorConfigPath = os.path.join(CONFIG_DIR, 'doorSettings.json')
		cameraConfigPath = os.path.join(CONFIG_DIR, 'cameraSettings.json')
		pushbulletConfigPath = os.path.join(CONFIG_DIR, 'pushbulletSettings.json')
		self.dc = DoorController(doorConfigPath, cameraConfigPath, pushbulletConfigPath, skipLogging=True)

	def __enter__(self):
		return self.dc

	def __exit__(self, type, value, traceback):
		self.dc.cleanup()


def test_startStop():
	"""
	Test that we can start the door controller and stop it by setting the monitor flag to False
	"""
	dc = DoorControllerTest()

	with dc as door:
		door.start()
		door.monitor = False
