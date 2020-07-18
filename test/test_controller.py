import json
import logging
import os
import time
import timeit
from typing import List

import pytest

from library import GarageDoorStates
from library.communication.mqtt import MQTTClient
from library.config import ConfigurationHandler, SENSORCLASSES, PubSubKeys
from library.config.gpio_driver import ConfigKeys as GPIODriverConfigKeys
from library.config.mqtt import MQTTConfig
from library.data import DatabaseKeys
from library.data.database import get_database_path

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError, ModuleNotFoundError):  # pragma: no cover
    from library.sensors import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Failed to import RPi.GPIO - using mock library")
    from library.mock.mock_gpio import GPIO

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH, debug=True)

MESSAGE = None
MESSAGE_RECEIVED = False
MOCK_GPIO_INPUT = 0
MAX_WAIT_SECONDS = 2.5
MAX_ENV_WAIT_SECONDS = MAX_WAIT_SECONDS * 3

MOCK_GPIO_STATE = None


@pytest.fixture
def mock_get_latest_db_entry(mocker):
    mocker.patch("library.controllers.camera.PiCameraController.get_latest_db_entry", return_value=None)


@pytest.fixture
def mock_db_enabled_pushbullet(mocker):
    mocker.patch("library.controllers.pushbullet.PushBulletController.db_enabled", return_value=False)


@pytest.fixture
def mock_db_enabled_camera(mocker):
    mocker.patch("library.controllers.camera.PiCameraController.db_enabled", return_value=False)


@pytest.fixture
def mock_should_capture_from_command(mocker):
    mocker.patch("library.controllers.camera.PiCameraController.should_capture_from_command", return_value=True)


@pytest.fixture
def mock_should_toggle_from_command(mocker):
    mocker.patch("library.controllers.gpio_driver.GPIODriverController.should_toggle_from_command", return_value=True)


@pytest.fixture
def mock_capture_loop(mocker):
    mocker.patch("library.controllers.camera.PiCameraController.capture_loop", return_value=None)


@pytest.fixture
def mock_toggle_loop(mocker):
    mocker.patch("library.controllers.gpio_driver.GPIODriverController.toggle_loop", return_value=None)


class TestTopic:
    __test__ = False

    def __init__(self, topic, payload, capture):
        self.topic = topic
        self.payload = payload
        self.capture = capture


def setup_module():
    for sensor in CONFIGURATION_HANDLER:
        if sensor.db_enabled:
            path = get_database_path(sensor.db.name)
            if os.path.exists(path):
                os.remove(path)


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


def mock_gpio_write(direction):
    global MOCK_GPIO_STATE
    MOCK_GPIO_STATE = direction


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

    @pytest.mark.usefixtures("mock_should_capture_from_command")
    def test_thread(self):
        """
        Test that the thread starts and stops properly
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""

        controller.start()
        assert controller.running
        wait_n_seconds(0.25)
        assert controller.running
        controller.running = False
        start = time.time()
        while time.time() - start < MAX_WAIT_SECONDS:
            if not controller.thread.is_alive():
                break
        assert not controller.thread.is_alive()

    @pytest.mark.usefixtures("mock_should_capture_from_command")
    @pytest.mark.parametrize(
        "force_cmd",
        [
            True,
            False
        ]
    )
    def test_capture(self, force_cmd):
        """
        Test that the capture loop creates the image
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""

        config = controller.config
        """ @type: library.config.camera.CameraConfig """
        expected_path = config.capture_path
        if os.path.exists(expected_path):
            os.remove(expected_path)
        controller.capture_loop(force=force_cmd)
        assert os.path.exists(expected_path)

    def test_should_capture_from_command_db(self):
        """
        Test that should_capture_from_command properly reads database
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""

        topic_open = TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.OPEN}, True)
        with controller.db as db:
            # Set up for test
            controller.last_capture_timestamp = -999
            db.delete_all_except_last_n_records(0)

            # No records - capture
            assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)

            # One record with captured=False - capture
            db.add_data([0, GarageDoorStates.OPEN, int(False), int(False)])
            assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)
            db.delete_all_except_last_n_records(0)

            # One record with captured=True - do not capture
            db.add_data([0, GarageDoorStates.OPEN, int(True), int(False)])
            assert not controller.should_capture_from_command(topic_open.topic, topic_open.payload)
            db.delete_all_except_last_n_records(0)

            # Multiple records - capture then don't
            db.add_data([0, GarageDoorStates.CLOSED, int(False), int(False)])
            db.add_data([1, GarageDoorStates.OPEN, int(False), int(False)])
            assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)
            controller.update_database_entry()
            assert not controller.should_capture_from_command(topic_open.topic, topic_open.payload)

    @pytest.mark.usefixtures("mock_db_enabled_camera")
    @pytest.mark.parametrize(
        "topic",
        [
            TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.OPEN}, True),
            TestTopic("home-assistant/pytest/gpio_monitor/state", {"state": GarageDoorStates.CLOSED}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": True, "delay": 1.0}, PubSubKeys.FORCE),
            TestTopic("home-assistant/pytest/camera", {"delay": 1.0}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": False}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": False, "force": "True"}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": False, "force": "False"}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": False, "force": "Force"}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": False, "force": "Force", "delay": 1.0}, False),
            TestTopic("home-assistant/pytest/camera", {"capture": True, "force": "Force", "delay": 1.0}, PubSubKeys.FORCE),
            TestTopic("fake_topic", {"capture": False}, False),
        ]
    )
    def test_should_capture_from_command_nodb(self, topic):
        """
        Test should_capture_from_command works without database access
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""
        controller.db.delete_all_except_last_n_records(0)

        assert controller.should_capture_from_command(topic.topic, topic.payload) == topic.capture

    @pytest.mark.usefixtures("mock_should_capture_from_command", "mock_capture_loop")
    def test_mqtt(self):
        """
        Test that MQTT topic subscription works and published messages are received
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""

        global MESSAGE
        MESSAGE = False
        topics = [x.name for x in controller.config.mqtt_topic]
        client = get_mqtt_client(controller.config.mqtt_config, topics)

        controller.setup()
        topic = controller.config.mqtt_topic[0]
        payload = topic.payload()
        controller.mqtt.single(topic.name, payload, qos=2)
        i = 0
        delay_time = 0.001
        while not MESSAGE:
            time.sleep(delay_time)
            i += 1
            if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                assert False, "Wait time exceeded!"
        controller.stop()
        client.disconnect()
        assert MESSAGE


class TestGPIODriverController:

    @pytest.mark.usefixtures("mock_should_toggle_from_command")
    def test_thread(self):
        """
        Test that the thread starts and stops properly
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_DRIVER)
        """ @type: library.controllers.gpio_driver.GPIODriverController """

        controller.start()
        assert controller.running

        wait_n_seconds(0.25)
        assert controller.running

        controller.running = False
        start = time.time()
        while time.time() - start < MAX_WAIT_SECONDS:
            if not controller.thread.is_alive():
                break
        assert not controller.thread.is_alive()

    @pytest.mark.usefixtures("mock_should_toggle_from_command")
    def test_toggle(self, monkeypatch):
        global MOCK_GPIO_STATE
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_DRIVER)
        """ @type: library.controllers.gpio_driver.GPIODriverController """
        monkeypatch.setattr(controller.sensor, "write", mock_gpio_write)

        controller.sensor.config.config[GPIODriverConfigKeys.ACTIVE_DIRECTION] = "HIGH"
        controller.toggle_loop()
        assert MOCK_GPIO_STATE == GPIO.LOW

        controller.sensor.config.config[GPIODriverConfigKeys.ACTIVE_DIRECTION] = "LOW"
        controller.toggle_loop()
        assert MOCK_GPIO_STATE == GPIO.HIGH

    def test_should_toggle_from_command(self):
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_DRIVER)
        """ @type: library.controllers.gpio_driver.GPIODriverController """

        topic = TestTopic("home-assistant/pytest/gpio_driver", {"control": "TOGGLE"}, True)
        assert controller.should_toggle_from_command(topic.topic, topic.payload)

        topic.payload = {"control": "HELLO"}
        assert not controller.should_toggle_from_command(topic.topic, topic.payload)


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

    @pytest.mark.usefixtures("mock_db_enabled_pushbullet")
    def test_mqtt(self, monkeypatch):
        """
        Test that controller subscribes to topics and receives published messages
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
        """ @type: library.controllers.pushbullet.PushBulletController"""

        global MESSAGE
        global text_sent
        global file_sent
        text_sent, file_sent = False, False

        MESSAGE = False
        topics = [x.name for x in controller.config.mqtt_topic]
        client = get_mqtt_client(controller.config.mqtt_config, topics)

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

        def mock_should_image_notify(force=True):
            return force

        monkeypatch.setattr(controller, "should_text_notify", lambda: True)
        monkeypatch.setattr(controller, "should_image_notify", mock_should_image_notify)
        monkeypatch.setattr(controller.notifier, "send_file", mock_send_file)
        monkeypatch.setattr(controller.notifier, "send_text", mock_send_text)

        topic_state = controller.config.mqtt_topic[0]
        topic_publish = controller.config.mqtt_topic[1]
        payload_closed = json.dumps(topic_state.payload())
        payload_capture = topic_publish.payload()
        payload_capture[PubSubKeys.FORCE] = True
        payload_capture = json.dumps(payload_capture)
        controller.start()

        for payload in [payload_closed, payload_capture]:
            controller.mqtt.single(topic_state.name, payload, qos=2)
            wait_n_seconds(2)

        start = timeit.default_timer()
        now = start
        while not (text_sent and file_sent) and now - start < MAX_WAIT_SECONDS:
            now = timeit.default_timer()

        if not text_sent or not file_sent:
            raise Exception(f"Messages not received! file: {file_sent}, text: {text_sent}")

        controller.stop()
        client.disconnect()
        assert MESSAGE

    def test_should_text_notify(self):
        """
        Test the should_text_notify method
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
        """ @type: library.controllers.pushbullet.PushBulletController"""

        # clear DB entries
        with controller.db as db:
            db.delete_all_except_last_n_records(0)

            # Notify if no DB entries
            assert controller.should_text_notify()

            # Notify if last entry is old
            db.add_data([0, GarageDoorStates.CLOSED, int(False), int(False)])
            assert controller.should_text_notify()
            db.delete_all_except_last_n_records(0)

            # Notify if only one DB entry
            cur_time = int(time.time())
            i = 0
            db.add_data([cur_time + i, GarageDoorStates.CLOSED, int(False), int(False)])
            assert controller.should_text_notify()

            # Don't notify if last two entries are "CLOSED"
            i += 1
            db.add_data([cur_time + i, GarageDoorStates.CLOSED, int(False), int(False)])
            assert not controller.should_text_notify()

            # Don't notify if last entry is "OPEN"
            i += 1
            db.add_data([cur_time + i, GarageDoorStates.OPEN, int(False), int(False)])
            assert not controller.should_text_notify()

            # Notify if last entry is CLOSED and previous two are not both CLOSED or OPEN
            i += 1
            db.add_data([cur_time + i, GarageDoorStates.CLOSED, int(False), int(False)])
            assert controller.should_text_notify()

    def test_should_image_notify(self):
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
        """ @type: library.controllers.pushbullet.PushBulletController"""

        # clear DB entries
        with controller.db as db:
            db.delete_all_except_last_n_records(0)

            # Notify if no entries
            assert controller.should_image_notify()

            # Don't notify if latest entry is closed
            db.add_data([0, GarageDoorStates.CLOSED, int(False), int(False)])
            assert not controller.should_image_notify()
            db.delete_all_except_last_n_records(0)

            # Notify if last entry is open and no notification
            i = 0
            db.add_data([i, GarageDoorStates.OPEN, int(False), int(False)])
            assert controller.should_image_notify()

            # Don't notify if last entry is open but has been notified
            i += 1
            db.add_data([i, GarageDoorStates.OPEN, int(False), int(True)])
            assert not controller.should_image_notify()

            # Notify if force no matter what
            assert controller.should_image_notify(force=True)
