import pytest
import time
import json
import os

from library.config import ConfigurationHandler, SENSOR_CLASSES
from library.communication.mqtt import MQTTClient
from library.communication.pushbullet import PushbulletTextNotify, PushbulletImageNotify

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


def teardown_module():
    for sensor in CONFIGURATION_HANDLER:
        sensor.cleanup()


def get_mqtt_client(mqtt_config, topics, message):
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
    client.connect(host=mqtt_config.broker, port=mqtt_config.port)
    client.loop_start()
    return client


def mock_gpio_read():
    global MOCK_GPIO_INPUT
    MOCK_GPIO_INPUT = 1 if MOCK_GPIO_INPUT == 0 else 0
    return bool(MOCK_GPIO_INPUT)


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
            TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": "Open"}, True),
            TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": "Closed"}, False),
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


class Test_PushulletController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSOR_CLASSES.PUSHBULLET)
    """ @type: library.controllers.pushbullet.PushbulletController"""
    def test_thread(self):
        self.controller.start()
        assert self.controller.running
        self.controller.stop()
        assert not self.controller.running

    def test_publish(self, monkeypatch):
        global message
        message = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics, message)

        def mock_upload_file(f, file_name, file_type="jpeg"):
            file_url = f"http://some.fake.url/{file_name}"
            print(f"Fake uploaded {file_name}")
            return {"file_type": file_type, "file_url": file_url, "file_name": file_name}

        def mock_push_file(file_name, file_url, file_type):
            print(f"Fake pushed {file_name}")
            return {}

        def mock_push_note(title, body):
            print(f"Fake pushed: {title}: {body}")
            return {"type": "note", "title": title, "body": body}

        monkeypatch.setattr(PushbulletImageNotify, "upload_file", mock_upload_file)
        monkeypatch.setattr(PushbulletImageNotify, "push_file", mock_push_file)
        monkeypatch.setattr(PushbulletTextNotify, "push_note", mock_push_note)

        topic = self.controller.config.mqtt_topic[0]
        payload = json.dumps(topic.payload())

        payload_closed = payload.replace("Open", "").replace("|", "")
        payload_open = payload.replace("Closed", "").replace("|", "")
        for payload in [payload_closed, payload_open]:
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
