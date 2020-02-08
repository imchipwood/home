import pytest
import time
import timeit
import json
import os

from library import GarageDoorStates
from library.config import ConfigurationHandler, SENSOR_CLASSES
from library.communication.mqtt import MQTTClient

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH, debug=True)

MESSAGE_RECEIVED = False
MOCK_GPIO_INPUT = 0
MAX_WAIT_SECONDS = 2.5
MAX_ENV_WAIT_SECONDS = MAX_WAIT_SECONDS * 3


class TestTopic:
    def __init__(self, topic, payload, capture):
        self.topic = topic
        self.payload = payload
        self.capture = capture


# def teardown_module():
#     for sensor in CONFIGURATION_HANDLER:
#         sensor.cleanup()


def get_mqtt_client(mqtt_config, topics, message):
    client = MQTTClient("test")

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            raise Exception("Failed to connect to MQTT")
        print("TEST_MQTT: CONNECTED, subscribing now")
        client.subscribe([(x, 1) for x in topics])

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        print(f"TEST_MQTT: Received payload: {payload}")
        global message
        message = True

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host=mqtt_config.broker, port=mqtt_config.port)
    client.loop_start()
    return client


def mock_gpio_read():
    global MOCK_GPIO_INPUT
    MOCK_GPIO_INPUT = 1 if MOCK_GPIO_INPUT == 0 else 0
    return bool(MOCK_GPIO_INPUT)


def wait_n_seconds(n):
    start = timeit.default_timer()
    now = timeit.default_timer()
    while now - start < n:
        now = timeit.default_timer()


class Test_EnvironmentController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.ENVIRONMENT)
    """ @type: library.controllers.environment.EnvironmentController """
    def test_thread(self):
        self.controller.sensor.reset_readings()
        self.controller.start()
        assert self.controller.running
        self.controller.cleanup()
        assert not self.controller.running
        i = 0
        while self.controller.thread.is_alive() or self.controller.sensor.humidity == -999.0:
            time.sleep(0.001)
            i += 1
            if i > MAX_ENV_WAIT_SECONDS * 1000:
                assert False, "Thread didn't stop!"

    def test_publish(self):
        global message
        message = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics, message)
        self.controller.publish(temperature=123.123, humidity=50.05, units="Fahrenheit")
        i = 0
        while not message:
            time.sleep(0.001)
            i += 1
            if i > MAX_WAIT_SECONDS * 1000:
                raise Exception("Wait time exceeded!")
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

    @pytest.mark.parametrize(
        "topic",
        [
            TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.OPEN}, True),
            TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.CLOSED}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": True, "delay": 1.0}, True),
            TestTopic("home-assistant/pytest/camera", {"delay": 1.0}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": False}, False),
            TestTopic("fake_topic", {"capture": False}, False),
        ]
    )
    def test_should_capture_from_command(self, topic):
        assert self.controller.should_capture_from_command(topic.topic, topic.payload) == topic.capture

    def test_mqtt(self, monkeypatch):
        global message
        message = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics, message)

        def mock_start_thread():
            self.controller.mqtt.loop_start()

        monkeypatch.setattr(self.controller, "_start_thread", mock_start_thread)

        self.controller.connect_mqtt()
        topic = self.controller.config.mqtt_topic[0]
        payload = topic.payload()
        self.controller.mqtt.single(topic.name, payload)
        i = 0
        while not message:
            time.sleep(0.001)
            i += 1
            if i > MAX_WAIT_SECONDS * 1000:
                raise Exception("Wait time exceeded!")
        self.controller.stop()
        client.disconnect()
        assert message


class Test_GPIOMonitorController:
    def test_thread(self, monkeypatch):
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(self.controller.sensor, "read", mock_gpio_read)
        self.controller.start()
        assert self.controller.running
        time.sleep(0.1)
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()

    def test_publish(self, monkeypatch):
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(self.controller.sensor, "read", mock_gpio_read)

        global message
        message = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics, message)

        self.controller.publish_event(self.controller.sensor.config.pin)
        i = 0
        while not message:
            time.sleep(0.001)
            i += 1
            if i > MAX_WAIT_SECONDS * 1000:
                raise Exception("Wait time exceeded!")
        client.disconnect()
        assert message


class Test_PushbulletController:
    def test_publish(self, monkeypatch):
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.PUSHBULLET)
        """ @type: library.controllers.pushbullet.PushbulletController"""

        global message
        global text_sent
        global file_sent
        text_sent, file_sent = False, False

        message = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics, message)

        def mock_send_file(file_path):
            global file_sent
            file_sent = True
            print("SEND FILE")
            print(f"Fake uploaded {file_path}")

        def mock_send_text(title, body):
            global text_sent
            text_sent = True
            print("SEND TEXT")
            print(f"Fake pushed: {title}: {body}")

        def mock_wait_for_file_refresh(file_path):
            return True

        monkeypatch.setattr(self.controller.notifier, "send_file", mock_send_file)
        monkeypatch.setattr(self.controller.notifier, "send_text", mock_send_text)
        monkeypatch.setattr(self.controller, "wait_for_file_refresh", mock_wait_for_file_refresh)

        topic = self.controller.config.mqtt_topic[0]
        payload = json.dumps(topic.payload())

        payload_closed = payload.replace(GarageDoorStates.OPEN, "").replace("|", "")
        payload_open = payload.replace(GarageDoorStates.CLOSED, "").replace("|", "")
        self.controller.start()

        for payload in [payload_open, payload_closed]:
            self.controller.mqtt.single(topic.name, payload)
            start = timeit.default_timer()
            now = timeit.default_timer()
            while now - start < 2:
                now = timeit.default_timer()

        start = timeit.default_timer()
        now = timeit.default_timer()
        while not (text_sent or file_sent) and now - start < MAX_WAIT_SECONDS * 2:
            now = timeit.default_timer()

        if not text_sent or not file_sent:
            raise Exception(f"Messages not received! file: {file_sent}, text: {text_sent}")

        self.controller.stop()
        client.disconnect()
        assert message
