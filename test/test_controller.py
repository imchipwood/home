import time

from library.config.topconfig import ConfigurationHandler

CONFIG_PATH = "test.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)
CONTROLLER = CONFIGURATION_HANDLER.get_sensor_controller('environment')


class TestEnvironmentController:
	def test_thread(self):
		CONTROLLER.start()
		assert CONTROLLER.running
		CONTROLLER.cleanup()
		assert not CONTROLLER.running
		i = 0
		while CONTROLLER.thread.isAlive():
			time.sleep(0.01)
			i += 1
			if i > 10:
				assert False, "Thread didn't stop!"
