import json
import logging
import os
import time
import timeit
from typing import List

import pytest

from library import GarageDoorStates, GPIODriverCommands
from library.communication.mqtt import MQTTClient
from library.config import ConfigurationHandler, SENSORCLASSES, PubSubKeys, DatabaseKeys
from library.config.mqtt import MQTTConfig
from util import fix_mqtt_topic_subscribe_name

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
MOCK_GPIO_INPUT = 0
MAX_WAIT_SECONDS = 2.5
MAX_ENV_WAIT_SECONDS = MAX_WAIT_SECONDS * 3

MOCK_TEXT_SENT = None
MOCK_FILE_SENT = None
GPIO_ON_RECEIVED = None
GPIO_OFF_RECEIVED = None
GPIO_TOGGLE_RECEIVED = None


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
def mock_get_gpio_command_from_message(mocker):
    mocker.patch("library.controllers.gpio_driver.GPIODriverController.get_gpio_command_from_message", return_value=GPIODriverCommands.TOGGLE)


@pytest.fixture
def mock_capture_loop(mocker):
    mocker.patch("library.controllers.camera.PiCameraController.capture_loop", return_value=None)


@pytest.fixture
def mock_gpiodriver_toggle(mocker):

    def setMessage():
        global GPIO_TOGGLE_RECEIVED
        GPIO_TOGGLE_RECEIVED = GPIODriverCommands.TOGGLE
        print(f"Received command: {GPIO_TOGGLE_RECEIVED}")

    mocker.patch("library.sensors.gpio_driver.GPIODriver.toggle", side_effect=setMessage)


@pytest.fixture
def mock_gpiodriver_write_on(mocker):

    def setMessage():
        global GPIO_ON_RECEIVED
        GPIO_ON_RECEIVED = GPIODriverCommands.ON
        print(f"Received command: {GPIO_ON_RECEIVED}")

    mocker.patch("library.sensors.gpio_driver.GPIODriver.write_on", side_effect=setMessage)


@pytest.fixture
def mock_gpiodriver_write_off(mocker):

    def setMessage():
        global GPIO_OFF_RECEIVED
        GPIO_OFF_RECEIVED = GPIODriverCommands.OFF
        print(f"Received command: {GPIO_OFF_RECEIVED}")

    mocker.patch("library.sensors.gpio_driver.GPIODriver.write_off", side_effect=setMessage)


class TestTopic:
    __test__ = False

    def __init__(self, topic, payload, capture):
        self.topic = topic
        self.payload = payload
        self.capture = capture


def setup_module():
    for sensor in CONFIGURATION_HANDLER:
        if sensor and sensor.db_enabled:
            with sensor.db as db:
                for table in reversed(list(db.tables.values())):
                    table.drop()


def teardown_module():
    for sensor in CONFIGURATION_HANDLER:
        if sensor:
            sensor.cleanup()
            if sensor.db_enabled:
                with sensor.db as db:
                    for table in reversed(list(db.tables.values())):
                        table.drop()


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

    def on_subscribe(client, userdata, mid, granted_qos):
        print(f"TEST_MQTT: (SUBSCRIBE) client: {client._client_id}, mid {mid}, granted_qos: {granted_qos}")

    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        print(f"TEST_MQTT: Received payload: {payload}, QOS: {msg.qos}")
        global MESSAGE
        MESSAGE = True

    mqtt_client.on_subscribe = on_subscribe
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

    def test_thread(self, monkeypatch):
        """
        Test that the thread starts and stops properly
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.ENVIRONMENT)
        """ @type: library.controllers.environment.EnvironmentController """

        def mock_publish(humidity, temperature, units):
            return

        def mock_read():
            return 75.0, 40.0

        monkeypatch.setattr(controller, "publish", mock_publish)
        monkeypatch.setattr(controller.sensor, "read", mock_read)

        controller.sensor.reset_readings()
        controller.start()
        assert controller.running

        wait_n_seconds(0.1)
        controller.cleanup()
        assert not controller.running

        i = 0
        delay_time = 0.001
        while controller.thread.is_alive() or controller.sensor.humidity == -999.0:
            time.sleep(delay_time)
            i += 1
            if i > MAX_ENV_WAIT_SECONDS * (1.0 / delay_time):
                assert False, "Thread didn't stop!"

    def test_publish(self):
        """
        Test that publish method actually publishes data
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.ENVIRONMENT)
        """ @type: library.controllers.environment.EnvironmentController """

        global MESSAGE
        MESSAGE = False

        topics = [x.name for x in controller.config.mqtt_topic]
        client = get_mqtt_client(controller.config.mqtt_config, topics)
        controller.publish(temperature=123.123, humidity=50.05, units="Fahrenheit")

        i = 0
        delay_time = 0.001
        try:
            while not MESSAGE:
                time.sleep(delay_time)
                i += 1
                if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                    assert False, "Wait time exceeded!"
        finally:
            client.disconnect()
            controller.cleanup()
        assert MESSAGE


class TestMqttEnvironmentController:
    def test_thread(self):
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.MQTT_ENVIRONMENT)
        """ @type: library.controllers.mqtt_environment.MqttEnvironmentController """

        controller.start()
        assert controller.running
        wait_n_seconds(0.25)

        assert controller.running
        controller.cleanup()

        start = time.time()
        while controller.thread.is_alive() and time.time() - start < MAX_WAIT_SECONDS:
            pass
        assert not controller.thread.is_alive(), "Thread didn't stop!"

    def test_mqtt(self):
        """
        Test that MQTT topic subscription works and published messages are received
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.MQTT_ENVIRONMENT)
        """ @type: library.controllers.mqtt_environment.MqttEnvironmentController """

        global MESSAGE
        MESSAGE = False
        topics = [x.name for x in controller.config.mqtt_topic]
        client = get_mqtt_client(controller.config.mqtt_config, topics)

        # clear db
        with controller.db as db:
            db.get_table(controller.db_table_name).delete_all_except_last_n_records(0)

        controller.setup()
        topic = controller.config.mqtt_topic[0]
        topic_name = fix_mqtt_topic_subscribe_name(topic)
        payload = topic.payload()
        client.single(
            topic_name,
            payload,
            retain=False,
            qos=2,
            hostname=controller.config.mqtt_config.broker,
            port=controller.config.mqtt_config.port
        )
        i = 0
        delay_time = 0.001
        try:
            while not MESSAGE:
                time.sleep(delay_time)
                i += 1
                if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                    assert False, "Wait time exceeded!"
        finally:
            controller.cleanup()
            client.disconnect()
        assert MESSAGE

        # also check db has a new entry
        with controller.db as db:
            entry = db.get_table(controller.db_table_name).get_latest_record()
            assert entry, "expected entry in database"


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
        controller.cleanup()

        start = time.time()
        while controller.thread.is_alive() and time.time() - start < MAX_WAIT_SECONDS:
            pass
        assert not controller.thread.is_alive(), "Thread didn't stop!"

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

        convo_id = "1234567890"

        try:
            controller.capture_loop(force=force_cmd, convo_id=convo_id)
            assert os.path.exists(expected_path)
        finally:
            controller.cleanup()

    def test_should_capture_from_command_db(self):
        """
        Test that should_capture_from_command properly reads database
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""

        convo_id = "1234567890"
        convo_id2 = "0987654321"
        topic_open = TestTopic("hass/pytest/gpio/state", {PubSubKeys.STATE: GarageDoorStates.OPEN, PubSubKeys.ID: convo_id}, True)
        topic_open2 = TestTopic("hass/pytest/gpio/state", {PubSubKeys.STATE: GarageDoorStates.OPEN, PubSubKeys.ID: convo_id2}, True)
        try:
            table_name = controller.config.mqtt_config.db_table_name
            with controller.db as db:
                # Set up for test
                table = db.get_table(table_name)
                table.delete_all_except_last_n_records(0)

                # No records - capture
                assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)

                # One record with captured=False - capture
                table.add_data([0, GarageDoorStates.OPEN, convo_id, int(False), int(False)])
                assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)
                table.delete_all_except_last_n_records(0)

                # One record with captured=True - do not capture
                table.add_data([0, GarageDoorStates.OPEN, convo_id, int(True), int(False)])
                assert not controller.should_capture_from_command(topic_open.topic, topic_open.payload)
                table.delete_all_except_last_n_records(0)

                # Multiple records - capture then don't
                table.add_data([0, GarageDoorStates.CLOSED, convo_id, int(False), int(False)])
                table.add_data([1, GarageDoorStates.OPEN, convo_id, int(False), int(False)])
                assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)
                controller.update_database_entry(convo_id)
                assert not controller.should_capture_from_command(topic_open.topic, topic_open.payload)
                table.delete_all_except_last_n_records(0)

                # Multiple records with different IDs - test each ID
                table.add_data([0, GarageDoorStates.CLOSED, convo_id, int(False), int(False)])
                table.add_data([1, GarageDoorStates.OPEN, convo_id2, int(False), int(False)])
                assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)
                controller.update_database_entry(convo_id)
                assert not controller.should_capture_from_command(topic_open.topic, topic_open.payload)
                assert controller.should_capture_from_command(topic_open2.topic, topic_open2.payload)
                controller.update_database_entry(convo_id2)
                assert not controller.should_capture_from_command(topic_open2.topic, topic_open2.payload)

                # Multiple records with different IDs - new ID comes in
                table.delete_all_except_last_n_records(0)
                table.add_data([0, GarageDoorStates.CLOSED, "123", int(False), int(False)])
                table.add_data([1, GarageDoorStates.OPEN, "456", int(False), int(False)])
                assert controller.should_capture_from_command(topic_open.topic, topic_open.payload)

        finally:
            controller.cleanup()

    @pytest.mark.usefixtures("mock_db_enabled_camera")
    @pytest.mark.parametrize(
        "topic",
        [
            TestTopic("hass/pytest/gpio/state", {PubSubKeys.STATE: GarageDoorStates.OPEN}, True),
            TestTopic("hass/pytest/gpio/state", {PubSubKeys.STATE: GarageDoorStates.CLOSED}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: True, PubSubKeys.DELAY: 1.0}, PubSubKeys.FORCE),
            TestTopic("hass/pytest/camera", {PubSubKeys.DELAY: 1.0}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: False}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: False, PubSubKeys.FORCE: "True"}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: False, PubSubKeys.FORCE: "False"}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: False, PubSubKeys.FORCE: "Force"}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: False, PubSubKeys.FORCE: "Force", PubSubKeys.DELAY: 1.0}, False),
            TestTopic("hass/pytest/camera", {PubSubKeys.CAPTURE: True, PubSubKeys.FORCE: "Force", PubSubKeys.DELAY: 1.0}, PubSubKeys.FORCE),
            TestTopic("fake_topic", {PubSubKeys.CAPTURE: False}, False),
        ]
    )
    def test_should_capture_from_command_nodb(self, topic):
        """
        Test should_capture_from_command works without database access
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.CAMERA)
        """ @type: library.controllers.camera.PiCameraController"""
        controller.db_table.delete_all_except_last_n_records(0)

        try:
            assert controller.should_capture_from_command(topic.topic, topic.payload) == topic.capture
        finally:
            controller.cleanup()

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
        topic_name = fix_mqtt_topic_subscribe_name(topic)
        payload = topic.payload()
        client.single(
            topic_name,
            payload,
            retain=False,
            qos=2,
            hostname=controller.config.mqtt_config.broker,
            port=controller.config.mqtt_config.port
        )
        i = 0
        delay_time = 0.001
        try:
            while not MESSAGE:
                time.sleep(delay_time)
                i += 1
                if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                    assert False, "Wait time exceeded!"
        finally:
            controller.cleanup()
            client.disconnect()
        assert MESSAGE


class TestGPIODriverController:

    @pytest.mark.usefixtures("mock_get_gpio_command_from_message")
    def test_thread(self):
        """
        Test that the thread starts and stops properly
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_DRIVER)
        """ @type: library.controllers.gpio_driver.GPIODriverController """

        try:
            controller.start()
            assert controller.running

            wait_n_seconds(0.25)
            assert controller.running

            controller.cleanup()
            assert not controller.running

            start = time.time()
            while controller.thread.is_alive() and time.time() - start < MAX_WAIT_SECONDS:
                pass
            assert not controller.thread.is_alive(), "Thread didn't stop!"
        finally:
            controller.cleanup()

    def test_get_gpio_command_from_message(self):
        """
        Test that MQTT payloads result in expected commands
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_DRIVER)
        """ @type: library.controllers.gpio_driver.GPIODriverController """

        try:
            topic = TestTopic("hass/pytest/gpio/driver", {PubSubKeys.CONTROL: GPIODriverCommands.TOGGLE}, True)
            assert controller.get_gpio_command_from_message(topic.topic, topic.payload) == GPIODriverCommands.TOGGLE

            topic = TestTopic("hass/pytest/gpio/driver", {PubSubKeys.CONTROL: GPIODriverCommands.ON}, True)
            assert controller.get_gpio_command_from_message(topic.topic, topic.payload) == GPIODriverCommands.ON

            topic = TestTopic("hass/pytest/gpio/driver", {PubSubKeys.CONTROL: GPIODriverCommands.OFF}, True)
            assert controller.get_gpio_command_from_message(topic.topic, topic.payload) == GPIODriverCommands.OFF

            topic.payload = {PubSubKeys.CONTROL: "HELLO"}
            assert controller.get_gpio_command_from_message(topic.topic, topic.payload) is None

        finally:
            controller.cleanup()

    @pytest.mark.usefixtures("mock_gpiodriver_toggle", "mock_gpiodriver_write_on", "mock_gpiodriver_write_off")
    def test_mqtt(self):
        global GPIO_TOGGLE_RECEIVED
        global GPIO_ON_RECEIVED
        global GPIO_OFF_RECEIVED

        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_DRIVER)
        """ @type: library.controllers.gpio_driver.GPIODriverController """

        topics = [x.name for x in controller.config.mqtt_topic]
        client = get_mqtt_client(controller.config.mqtt_config, topics)

        try:
            controller.setup()
            topic = controller.config.mqtt_topic[0]

            commands = [GPIODriverCommands.TOGGLE, GPIODriverCommands.ON, GPIODriverCommands.OFF]
            for command in commands:
                payload = {PubSubKeys.CONTROL: command}
                client.single(
                    topic.name,
                    payload,
                    retain=False,
                    qos=0,
                    hostname=controller.config.mqtt_config.broker,
                    port=controller.config.mqtt_config.port
                )

            start = timeit.default_timer()
            while not all([GPIO_TOGGLE_RECEIVED, GPIO_ON_RECEIVED, GPIO_OFF_RECEIVED]) and \
                    timeit.default_timer() - start <= MAX_WAIT_SECONDS:
                pass

            mqtt_outputs = [GPIO_TOGGLE_RECEIVED, GPIO_ON_RECEIVED, GPIO_OFF_RECEIVED]
            missed_commands = [x[0] for x in zip(commands, mqtt_outputs) if not x[1]]
            assert not missed_commands, f"Wait time exceeded - missed commands: {missed_commands}!"

        finally:
            client.disconnect()
            controller.cleanup()


class TestGPIOMonitorController:

    def test_thread(self, monkeypatch):
        """
        Test that the thread starts and stops properly
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(controller.sensor, "read", mock_gpio_read)
        controller.start()
        assert controller.running
        wait_n_seconds(0.1)
        controller.cleanup()
        try:
            assert not controller.running
        finally:
            controller.cleanup()

    def test_database(self, monkeypatch):
        """
        Test that the database methods work
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(controller.sensor, "read", mock_gpio_read)

        try:
            # clear the database
            with controller.db as db:
                db.get_table(controller.db_table_name).delete_all_except_last_n_records(0)

            # Set the state to add an entry
            controller.state = not controller.state
            latest_state = controller.get_latest_db_entry(DatabaseKeys.STATE)
            assert latest_state == controller.get_state_as_string(controller.state)

            # Wait long enough for a unique timestamp for second entry
            latest_time = controller.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
            while int(time.time()) - latest_time < 1:
                pass
            controller.state = not controller.state

            # Check entries
            assert controller.get_latest_db_entry(DatabaseKeys.STATE) == str(controller)
            last_two = controller.get_last_two_db_entries()
            assert last_two[0] == controller.get_state_as_string(controller.state)
            assert last_two[1] == controller.get_state_as_string(not controller.state)
        finally:
            controller.cleanup()

    def test_publish(self, monkeypatch):
        """
        Test that publish method works
        """
        controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.GPIO_MONITOR)
        """ @type: library.controllers.gpio_monitor.GPIOMonitorController"""
        monkeypatch.setattr(controller.sensor, "read", mock_gpio_read)

        global MESSAGE
        MESSAGE = False
        topics = [x.name for x in controller.config.mqtt_topic]
        client = get_mqtt_client(controller.config.mqtt_config, topics)

        try:
            controller.publish()
            i = 0
            delay_time = 0.001

            while not MESSAGE:
                wait_n_seconds(delay_time)
                i += 1
                if i > MAX_WAIT_SECONDS * (1.0 / delay_time):
                    raise Exception("Wait time exceeded!")
        finally:
            controller.cleanup()
            client.disconnect()
        assert MESSAGE


# class TestPushBulletController:
#
#     @pytest.mark.usefixtures("mock_db_enabled_pushbullet")
#     def test_mqtt(self, monkeypatch):
#         """
#         Test that controller subscribes to topics and receives published messages
#         """
#         controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
#         """ @type: library.controllers.pushbullet.PushBulletController"""
#
#         global MESSAGE, MOCK_TEXT_SENT, MOCK_FILE_SENT
#         MESSAGE, MOCK_TEXT_SENT, MOCK_FILE_SENT = False, False, False
#
#         topics = [x.name for x in controller.config.mqtt_topic]
#         client = get_mqtt_client(controller.config.mqtt_config, topics)
#
#         def mock_send_file(file_path):
#             global MOCK_FILE_SENT
#             MOCK_FILE_SENT = True
#             print("SEND FILE")
#             print(f"Fake uploaded {file_path}")
#
#         def mock_send_text(title, body):
#             global MOCK_TEXT_SENT
#             MOCK_TEXT_SENT = True
#             print("SEND TEXT")
#             print(f"Fake pushed: {title}: {body}")
#
#         def mock_should_text_notify(convo_id):
#             return True
#
#         def mock_should_image_notify(convo_id, force=True):
#             return force
#
#         monkeypatch.setattr(controller, "should_text_notify", mock_should_text_notify)
#         monkeypatch.setattr(controller, "should_image_notify", mock_should_image_notify)
#         monkeypatch.setattr(controller.notifier, "send_file", mock_send_file)
#         monkeypatch.setattr(controller.notifier, "send_text", mock_send_text)
#
#         topic_state = controller.config.mqtt_topic[0]
#         topic_publish = controller.config.mqtt_topic[1]
#         payload_closed = json.dumps(topic_state.payload())
#         payload_capture = topic_publish.payload()
#         payload_capture[PubSubKeys.FORCE] = True
#         payload_capture = json.dumps(payload_capture)
#
#         try:
#             controller.start()
#
#             for topic, payload in [(topic_state.name, payload_closed), (topic_publish.name, payload_capture)]:
#                 client.single(
#                     topic,
#                     payload,
#                     retain=False,
#                     qos=2,
#                     hostname=controller.config.mqtt_config.broker,
#                     port=controller.config.mqtt_config.port
#                 )
#
#             start = timeit.default_timer()
#             now = start
#             while not (MOCK_TEXT_SENT and MOCK_FILE_SENT) and now - start < MAX_WAIT_SECONDS * 10:
#                 now = timeit.default_timer()
#
#             if not MOCK_TEXT_SENT or not MOCK_FILE_SENT:
#                 raise Exception(f"Messages not received! file: {MOCK_FILE_SENT}, text: {MOCK_TEXT_SENT}")
#
#         finally:
#             controller.stop()
#             client.disconnect()
#
#         assert MESSAGE
#
#     def test_should_text_notify(self):
#         """
#         Test the should_text_notify method
#         """
#         controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
#         """ @type: library.controllers.pushbullet.PushBulletController"""
#
#         convo_id = "1234567890"
#         convo_id2 = "0987654321"
#         convo_id3 = "0987654320"
#         try:
#             # clear DB entries
#             with controller.db as db:
#                 db.delete_all_except_last_n_records(0)
#
#                 # Notify if no DB entries
#                 assert controller.should_text_notify(convo_id)
#
#                 # Notify if target entry has not been notified
#                 db.add_data([0, GarageDoorStates.CLOSED, convo_id, int(False), int(False)])
#                 assert controller.should_text_notify(convo_id)
#
#                 # Don't notify if target entry is marked notified
#                 controller.mark_entry_notified(convo_id, GarageDoorStates.CLOSED)
#                 assert not controller.should_text_notify(convo_id)
#
#                 # Notify if entry doesn't exist
#                 assert controller.should_text_notify(convo_id2)
#
#                 # Don't notify if target entry is marked notified
#                 controller.mark_entry_notified(convo_id2, GarageDoorStates.CLOSED)
#                 assert not controller.should_text_notify(convo_id2)
#
#                 # Don't notify if target entry is for OPEN door
#                 db.add_data([1, GarageDoorStates.OPEN, convo_id3, int(False), int(False)])
#                 assert not controller.should_text_notify(convo_id3)
#
#         finally:
#             controller.cleanup()
#
#     def test_should_image_notify(self):
#         controller = CONFIGURATION_HANDLER.get_sensor_controller(SENSORCLASSES.PUSHBULLET)
#         """ @type: library.controllers.pushbullet.PushBulletController"""
#
#         convo_id = "1234567890"
#         # convo_id2 = "0987654321"
#         try:
#             # clear DB entries
#             with controller.db as db:
#                 db.delete_all_except_last_n_records(0)
#
#                 # Notify if no entries
#                 assert controller.should_image_notify(convo_id)
#
#                 # Don't notify if target entry is closed
#                 db.add_data([0, GarageDoorStates.CLOSED, convo_id, int(False), int(False)])
#                 assert not controller.should_image_notify(convo_id)
#                 db.delete_all_except_last_n_records(0)
#
#                 # Notify if target entry is open and no notification
#                 i = 0
#                 db.add_data([i, GarageDoorStates.OPEN, convo_id, int(False), int(False)])
#                 assert controller.should_image_notify(convo_id)
#
#                 # Don't notify if target entry is open but has been notified
#                 controller.mark_entry_notified(convo_id, GarageDoorStates.OPEN)
#                 # i += 1
#                 # db.add_data([i, GarageDoorStates.OPEN, convo_id, int(False), int(True)])
#                 assert not controller.should_image_notify(convo_id)
#
#                 # Notify if force no matter what
#                 assert controller.should_image_notify(convo_id, force=True)
#
#         finally:
#             controller.cleanup()
