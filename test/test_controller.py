import json
import os
import time
import timeit
from typing import List

import pytest

from library import GarageDoorStates
from library.communication.mqtt import MQTTClient
from library.config import ConfigurationHandler, SENSORCLASSES, ConfigKeys
from library.config.mqtt import MQTTConfig
from library.data import DatabaseKeys

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH, debug=True)

MESSAGE = None
MESSAGE_RECEIVED = False
MOCK_GPIO_INPUT = 0
MAX_WAIT_SECONDS = 2.5
MAX_ENV_WAIT_SECONDS = MAX_WAIT_SECONDS * 3


@pytest.fixture
def mock_get_latest_db_entry(mocker):
    mocker.patch("library.controllers.camera.PiCameraController.get_latest_db_entry", return_value=None)


class TestTopic:
    __test__ = False

    def __init__(self, topic, payload, capture):
        self.topic = topic
        self.payload = payload
        self.capture = capture


def teardown_module():
    for sensor in CONFIGURATION_HANDLER:
        sensor.cleanup()


def get_mqtt_client(mqtt_config: MQTTConfig, topics: List[str]) -> MQTTClient:
    """
    Helper method - returns MQTTClient with on_message event handler
    that sets message flag for testing if messages are received
    @param mqtt_config: MQTT config object
    @type mqtt_config: MQTTConfig
    @param topics: list of MQTT topics to subscribe to
    @type topics: list[str]
    @return: new MQTTClient
    @rtype: MQTTClient
    """
    mqtt_client = MQTTClient("test")

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            raise Exception("Failed to connect to MQTT")
        print("TEST_MQTT: CONNECTED, subscribing now")
        client.subscribe([(x, 0) for x in topics])

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        print(f"TEST_MQTT: Received payload: {payload}, QOS: {msg.qos}")
        global MESSAGE
        MESSAGE = True

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(host=mqtt_config.broker, port=mqtt_config.port)
    mqtt_client.loop_start()
    return mqtt_client


def mock_gpio_read():
    """
    mock GPIO read that alternates returned value
    @rtype: bool
    """
    global MOCK_GPIO_INPUT
    MOCK_GPIO_INPUT = 1 if MOCK_GPIO_INPUT == 0 else 0
    return bool(MOCK_GPIO_INPUT)


def wait_n_seconds(n):
    """
    wait some seconds
    @param n: number of seconds to wait
    @type n: float
    """
    start = timeit.default_timer()
    now = start
    while now - start < n:
        now = timeit.default_timer()


class TestEnvironmentController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.ENVIRONMENT)
    """ @type: library.controllers.environment.EnvironmentController """

    def test_thread(self, monkeypatch):
        """
        Test that the thread starts and stops properly
        """
        def mock_publish(humidity, temperature, units):
            return

        monkeypatch.setattr(self.controller, "publish", mock_publish)

        self.controller.sensor.reset_readings()
        self.controller.start()
        assert self.controller.running
        wait_n_seconds(0.1)
        self.controller.cleanup()
        assert not self.controller.running

        i = 0
        delay_time = 0.001
        while self.controller.thread.is_alive() or self.controller.sensor.humidity == -999.0:
            time.sleep(delay_time)
            i += 1
            if i > MAX_ENV_WAIT_SECONDS * (1.0 / delay_time):
                assert False, "Thread didn't stop!"

    def test_publish(self):
        """
        Test that publish method actually publishes data
        """
        global MESSAGE
        MESSAGE = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics)
        self.controller.publish(temperature=123.123, humidity=50.05, units="Fahrenheit")
        i = 0
        delay_time = 0.001
        while not MESSAGE:
            time.sleep(delay_time)
            i += 1
            if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                assert False, "Wait time exceeded!"
        client.disconnect()
        assert MESSAGE


class TestCameraController:
    controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
    """ @type: library.controllers.camera.PiCameraController"""

    def test_thread(self):
        """
        Test that the thread starts and stops properly
        """
        self.controller.start()
        assert self.controller.running
        wait_n_seconds(0.25)
        assert self.controller.running
        self.controller.running = False
        start = time.time()
        while time.time() - start < MAX_WAIT_SECONDS:
            if not self.controller.thread.is_alive():
                break
        assert not self.controller.thread.is_alive()

    def test_capture(self):
        """
        Test that the capture loop creates the image
        """
        config = self.controller.config
        """ @type: library.config.camera.CameraConfig """
        expected_path = config.capture_path
        if os.path.exists(expected_path):
            os.remove(expected_path)
        self.controller.capture_loop()
        assert os.path.exists(expected_path)

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
        """
        Test that should_capture_from_command properly detects when to capture
        """
        self.controller.last_capture_timestamp = -999
        assert self.controller.should_capture_from_command(topic.topic, topic.payload) == topic.capture

    def test_should_capture_from_command_db(self):
        """
        Test that should_capture_from_command properly reads database
        """
        topic_open = TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.OPEN}, True)
        with self.controller.db as db:
            # Set up for test
            self.controller.last_capture_timestamp = -999
            db.delete_all_except_last_n_records(0)

            db.add_data([0, GarageDoorStates.CLOSED])
            db.add_data([1, GarageDoorStates.OPEN])
            assert self.controller.should_capture_from_command(topic_open.topic, topic_open.payload)
            assert not self.controller.should_capture_from_command(topic_open.topic, topic_open.payload)

    @pytest.mark.usefixtures("mock_get_latest_db_entry")
    def test_should_capture_from_command_nodb(self):
        """
        Test should_capture_from_command works without database access
        """
        topic = TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.OPEN}, True)
        assert self.controller.should_capture_from_command(topic.topic, topic.payload) == topic.capture

    def test_mqtt(self, monkeypatch):
        """
        Test that MQTT topic subscription works and published messages are received
        """
        global MESSAGE
        MESSAGE = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics)

        def mock_should_capture_from_command(message_topic, message_data):
            return True

        def mock_capture_loop(delay=0):
            return

        monkeypatch.setattr(self.controller, "should_capture_from_command", mock_should_capture_from_command)
        monkeypatch.setattr(self.controller, "capture_loop", mock_capture_loop)

        self.controller.setup()
        topic = self.controller.config.mqtt_topic[0]
        payload = topic.payload()
        self.controller.mqtt.single(topic.name, payload, qos=2)
        i = 0
        delay_time = 0.001
        while not MESSAGE:
            time.sleep(delay_time)
            i += 1
            if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                assert False, "Wait time exceeded!"
        self.controller.stop()
        client.disconnect()
        assert MESSAGE


class TestGPIOMonitorController:

    def test_thread(self, monkeypatch):
        """
        Test that the thread starts and stops properly
        """
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(self.controller.sensor, "read", mock_gpio_read)
        self.controller.start()
        assert self.controller.running
        wait_n_seconds(0.1)
        self.controller.stop()
        assert not self.controller.running
        self.controller.cleanup()

    def test_database(self, monkeypatch):
        """
        Test that the database methods work
        """
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(self.controller.sensor, "read", mock_gpio_read)

        # clear the database
        with self.controller.db as db:
            db.delete_all_except_last_n_records(0)

        # Set the state to add an entry
        self.controller.state = not self.controller.state
        latest_state = self.controller.get_latest_db_entry(DatabaseKeys.STATE)
        assert latest_state == self.controller.get_state_as_string(self.controller.state)

        # Wait long enough for a unique timestamp for second entry
        latest_time = self.controller.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
        while int(time.time()) - latest_time < 1:
            pass
        self.controller.state = not self.controller.state

        # Check entries
        assert self.controller.get_latest_db_entry() == str(self.controller)
        last_two = self.controller.get_last_two_db_entries()
        assert last_two[0] == self.controller.get_state_as_string(self.controller.state)
        assert last_two[1] == self.controller.get_state_as_string(not self.controller.state)

    def test_publish(self, monkeypatch):
        """
        Test that publish method works
        """
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(self.controller.sensor, "read", mock_gpio_read)

        global MESSAGE
        MESSAGE = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics)

        self.controller.publish()
        i = 0
        delay_time = 0.001
        while not MESSAGE:
            wait_n_seconds(delay_time)
            i += 1
            if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                raise Exception("Wait time exceeded!")
        client.disconnect()
        assert MESSAGE


class TestPushBulletController:

    def test_mqtt(self, monkeypatch):
        """
        Test that controller subscribes to topics and receives published messages
        """
        self.controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
        """ @type: library.controllers.pushbullet.PushbulletController"""
        # don't use the database
        self.controller.config.config[ConfigKeys.DB] = None

        global MESSAGE
        global text_sent
        global file_sent
        text_sent, file_sent = False, False

        MESSAGE = False
        topics = [x.name for x in self.controller.config.mqtt_topic]
        client = get_mqtt_client(self.controller.config.mqtt_config, topics)

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

        monkeypatch.setattr(self.controller.notifier, "send_file", mock_send_file)
        monkeypatch.setattr(self.controller.notifier, "send_text", mock_send_text)

        topic_state = self.controller.config.mqtt_topic[0]
        topic_publish = self.controller.config.mqtt_topic[1]
        payload_closed = json.dumps(topic_state.payload())
        payload_capture = json.dumps(topic_publish.payload())
        self.controller.start()

        for payload in [payload_closed, payload_capture]:
            self.controller.mqtt.single(topic_state.name, payload, qos=2)
            wait_n_seconds(2)

        start = timeit.default_timer()
        now = start
        while not (text_sent or file_sent) and now - start < MAX_WAIT_SECONDS:
            now = timeit.default_timer()

        if not text_sent or not file_sent:
            raise Exception(f"Messages not received! file: {file_sent}, text: {text_sent}")

        self.controller.stop()
        client.disconnect()
        assert MESSAGE
