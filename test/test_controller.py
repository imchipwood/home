import time
from random import randint

from library.config import ConfigurationHandler, SENSOR_CLASSES

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)


class Test_EnvironmentController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.ENVIRONMENT)
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
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.CAMERA)
    """ @type: library.controllers.camera.PiCameraController"""

    def test_thread(self):
        self.controller.start()
        assert self.controller.running
        time.sleep(0.25)
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()

    def test_capture(self):
        self.controller.capture_loop()

    def test_mqtt(self, monkeypatch):

        def mock_start_thread():
            self.controller.mqtt.loop_start()

        monkeypatch.setattr(self.controller, "_start_thread", mock_start_thread)

        self.controller.connect_mqtt()
        topic = self.controller.config.mqtt_topic[0]
        payload = topic.payload()
        self.controller.mqtt.single(topic.name, payload)
        now = time.time()
        while time.time() < (now + 2):
            continue
        self.controller.stop()


class Test_GPIOMonitorController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.GPIO_MONITOR)
    """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""

    def test_thread(self, monkeypatch):
        def mock_input():
            return bool(randint(0, 1))
        monkeypatch.setattr(self.controller.sensor, "read", mock_input)
        self.controller.start()
        assert self.controller.running
        time.sleep(2)
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()
