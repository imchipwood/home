import time

from library.config import ConfigurationHandler

CONFIG_PATH = "test.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)


class Test_EnvironmentController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller('environment')
    """ @type: library.controllers.environment.EnvironmentController """
    def test_thread(self):
        self.controller.start()
        assert self.controller.running
        self.controller.cleanup()
        assert not self.controller.running
        i = 0
        while self.controller.thread.isAlive():
            time.sleep(0.01)
            i += 1
            if i > 1000:
                assert False, "Thread didn't stop!"

    def test_publish(self):
        self.controller.publish(temperature=123.123, humidity=50.05, units="Fahrenheit")


class Test_CameraController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller('camera')
    """ @type: library.controllers.camera.CameraController"""

    def test_thread(self):
        self.controller.start()
        assert self.controller.running
        self.controller.capture()
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()
