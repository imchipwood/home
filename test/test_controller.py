import time

from library.config import ConfigurationHandler

CONFIG_PATH = "test.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)
CONTROLLER = CONFIGURATION_HANDLER.get_sensor_controller('environment')
""" @type: library.controllers.environment.EnvironmentController """


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
            if i > 1000:
                assert False, "Thread didn't stop!"

    def test_publish(self):
        CONTROLLER.publish(temperature=123.123, humidity=50.05, units="Fahrenheit")
