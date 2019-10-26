import time
import os
from random import randint

from library.config import ConfigurationHandler, SENSOR_CLASSES
from library.communication.mqtt import MQTTClient

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH)

MESSAGE_RECEIVED = False


def teardown_module():
    for sensor in CONFIGURATION_HANDLER:
        sensor.cleanup()


def GetMqttClient(controller, topics, message):
    client = MQTTClient("test")

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            raise Exception("Failed to connect to MQTT")
        print("CONNECTED, subscribing now")
        client.subscribe([(x, 1) for x in topics])

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        print(f"Received payload: {payload}")
        global message
        message = True

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host=controller.config.mqtt_config.broker, port=controller.config.mqtt_config.port)
    client.loop_start()
    return client


mock_gpio_input = 0


def MOCK_GPIO_INPUT():
    global mock_gpio_input
    if mock_gpio_input == 0:
        mock_gpio_input = 1
    else:
        mock_gpio_input = 0
    return bool(mock_gpio_input)
    # return bool(randint(0, 1))


class Test_EnvironmentController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.ENVIRONMENT)
    """ @type: library.controllers.environment.EnvironmentController """
    def test_thread(self):
        self.controller.start()
        assert self.controller.running
        self.controller.cleanup()
        assert not self.controller.running
        i = 0
        while self.controller.thread.is_alive():
            time.sleep(0.01)
            i += 1
            if i > 1000:
                assert False, "Thread didn't stop!"

    def test_publish(self):
        global message
        message = False
        topics = [self.controller.config.mqtt_topic.name]
        client = GetMqttClient(self.controller, topics, message)
        self.controller.publish(temperature=123.123, humidity=50.05, units="Fahrenheit")
        time.sleep(0.1)
        client.disconnect()
        assert message


class Test_CameraController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.CAMERA)
    """ @type: library.controllers.camera.PiCameraController"""

    def test_thread(self):
        self.controller.start()
        assert self.controller.running
        # time.sleep(0.25)
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()

    def test_capture(self):
        config = self.controller.config
        """ @type: library.config.camera.CameraConfig """
        expectedPath = config.capture_path
        if os.path.exists(expectedPath):
            os.remove(expectedPath)
        self.controller.capture_loop()
        assert os.path.exists(expectedPath)

    def test_mqtt(self, monkeypatch):
        global message
        message = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = GetMqttClient(self.controller, topics, message)

        def mock_start_thread():
            self.controller.mqtt.loop_start()

        monkeypatch.setattr(self.controller, "_start_thread", mock_start_thread)

        self.controller.connect_mqtt()
        topic = self.controller.config.mqtt_topic[0]
        payload = topic.payload()
        self.controller.mqtt.single(topic.name, payload)
        # time.sleep(0.1)
        self.controller.stop()
        client.disconnect()
        assert message


class Test_GPIOMonitorController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.GPIO_MONITOR)
    """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""

    def test_thread(self, monkeypatch):
        monkeypatch.setattr(self.controller.sensor, "read", MOCK_GPIO_INPUT)
        self.controller.start()
        assert self.controller.running
        time.sleep(0.2)
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()
