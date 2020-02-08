"""
Camera Controller
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
from multiprocessing import Process
from threading import Thread

from library import GarageDoorStates
from library.data.database import Database
from library.sensors.camera import Camera

from library.controllers import BaseController, Get_Logger
from library.communication.mqtt import MQTTClient, MQTTError, Get_MQTT_Error_Message


class PiCameraController(BaseController):
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.camera.CameraConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config=config, debug=debug)

        self.logger = Get_Logger(__name__, debug, config.log)

        self.thread = Process(target=self.loop)

        self.mqtt = None
        """@type: MQTTClient"""

    # region Threading

    def setup(self):
        """
        Setup MQTT stuff
        """
        if self.config.mqtt_config:
            self.mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)
            self.logger.debug(f"MQTT Config: {self.mqtt}")
            self.mqtt.on_connect = self.on_connect
            self.mqtt.on_subscribe = self.on_subscribe
            self.mqtt.on_message = self.on_message

    def start(self):
        """
        Camera won't actually do threading - instead, we'll subscribe to an MQTT topic
        """
        self.logger.debug("Starting Camera MQTT connection")
        self.connect_mqtt()
        self.running = True

    def loop(self):
        """
        No actual threading for Camera
        """
        self.logger.debug("Starting MQTT loop")
        self.mqtt.loop_start()
        try:
            while True:
                continue
        except KeyboardInterrupt:
            self.logger.debug("KeyboardInterrupt, ignoring")

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down camera MQTT connection")
        try:
            if self.thread.is_alive():
                self.thread.terminate()
            self.mqtt.loop_stop()
            result = self.mqtt.disconnect()
            self.logger.debug(f"Disconnect result: {result}")
        except:
            self.logger.exception("Exception while disconnecting from MQTT - ignoring")
        self.running = False

    def _start_thread(self):
        """
        Start the thread
        """
        self.thread.start()

    # endregion Threading
    # region MQTT

    def connect_mqtt(self):
        """
        Simply connect to MQTT
        """
        if self.config.mqtt_topic and not self.running:
            self.logger.debug("in connect_mqtt")
            self.setup()
            result = self.mqtt.connect()
            self.logger.debug(f"Connect result: {result}")
            self._start_thread()

    def on_connect(self, client, userdata, flags, rc):
        """
        Event handler for MQTT connection
        """
        self.logger.info(f"mqtt: (CONNECT) client {client._client_id} received with code {rc}")

        # Check the connection results
        if rc != 0:
            message = Get_MQTT_Error_Message(rc)
            self.logger.error(message)
            raise MQTTError(f"on_connect 'rc' failure - {message}")

        # Nothing wrong with RC - subscribe to topic
        self.logger.info("Connection successful")
        # Subscribe to all topics simultaneously
        self.mqtt.subscribe([(x.name, 1) for x in self.config.mqtt_topic])

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """
        Simply log subscription status
        """
        self.logger.debug(f"mqtt: (SUBSCRIBE) client: {client._client_id}, mid {mid}, granted_qos: {granted_qos}")

    def on_message(self, client, userdata, msg):
        """
        Handler for new MQTT message
        """
        self.logger.debug(f"mqtt: (MESSAGE) client: {client._client_id}, topic: {msg.topic}, QOS: {msg.qos}")

        # Convert message to JSON
        payload = msg.payload.decode("utf-8")
        self.logger.debug(f"received payload: {payload}")
        try:
            message_data = json.loads(payload)
        except ValueError as e:
            self.logger.warning(f"Some error while converting string payload to dict: {e}")
            return

        # Check if it indicated a capture
        if self.should_capture_from_command(msg.topic, message_data):
            self.logger.info("Received capture command")
            # If no delay in message, pass in None - this will force camera to use
            # the delay defined in the config
            kwargs = {"delay": message_data.get("delay", None)}
            thread = Thread(target=self.capture_loop, kwargs=kwargs)
            thread.start()

    def should_capture_from_command(self, message_topic, message_data) -> bool:
        """
        Check if the message indicates a capture command
        @param message_topic: topic message came from
        @type message_topic: str
        @param message_data: message data as dict
        @type message_data: dict
        @return: whether or not to capture
        @rtype: bool
        """
        # Check all the topics we're subscribed to
        topic = self.config.mqtt_config.topics_subscribe.get(message_topic)
        if not topic:
            return False

        latest = None
        if self.config.db_name:
            self.logger.info(f"Opening DB {self.config.db_name}")
            with Database(self.config.db_name, self.config.db_columns) as db:
                self.logger.info(f"Opened DB {self.config.db_name}")
                last_two = db.get_last_n_records(2)
                if last_two:
                    latest = GarageDoorStates.OPEN if last_two[-1][1] == 1 else GarageDoorStates.CLOSED
                    self.logger.info(f"Latest state: {latest}")

        # Check the payload - assumes a single value
        for key, val in message_data.items():
            if key == "delay":
                continue
            message_val = topic.payload().get(key, None)

            if isinstance(message_val, str):
                message_val = message_val.lower()
                val = val.lower()

            if latest:
                return message_val == val and latest != val
            else:
                return message_val == val

        # Shouldn't ever get here but just in case...
        self.logger.warning("Didn't find expected payload - not capturing!")
        return False

    # endregion MQTT
    # region Camera

    def capture_loop(self, delay=0):
        """
        Simple method for capturing an image with PiCamera
        """
        with Camera(self.config, self.debug) as camera:
            camera.capture(delay=delay)

    # endregion Camera

    def cleanup(self):
        """
        Gracefully exit
        """
        super().cleanup()

    def __repr__(self):
        """
        @rtype: str
        """
        return f"{self.__class__}|{self.config.type}|{self.config.mqtt_config.client_id}"
