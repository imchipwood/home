"""
Simple gpio driver controller with MQTT support
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
import logging
import time
from threading import Thread

from library.communication.mqtt import MQTTClient, get_mqtt_error_message, MQTTError
from library.config import PubSubKeys
from library import GPIODriverCommands
from library.controllers import BaseController, get_logger
from library.data import DatabaseKeys
from library.data.database import Database
from library.sensors.gpio_driver import GPIODriver

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError, ModuleNotFoundError):  # pragma: no cover
    from library.sensors import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Failed to import RPi.GPIO - using mock library")
    from library.mock.mock_gpio import GPIO


class GPIODriverController(BaseController):

    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.gpio_driver.GPIODriverConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config, debug)

        self.logger = get_logger(__name__, debug, config.log)

        self.sensor = GPIODriver(
            self.config,
            debug=debug
        )
        self.thread = Thread(target=self.loop)

    def setup(self):
        """
        Setup MQTT stuff
        """
        if not self.mqtt:
            self.logger.warning("No MQTT client defined! Nothing for GPIO driver controller to do.")
            return

        self.logger.debug(f"MQTT Config: {self.mqtt}")
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_message = self.on_message

        self.logger.debug("Connecting MQTT")
        result = self.mqtt.connect()
        self.logger.debug(f"Connect result: {result}")
        self.mqtt.loop_start()

    def start(self):
        """
        Camera won't actually do threading - instead, we'll subscribe to an MQTT topic
        """
        self.logger.debug("Starting GPIO Driver MQTT connection")
        super().start()
        self.setup()
        self.thread.start()

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down GPIO Driver MQTT connection")
        super().stop()
        try:
            if self.mqtt:
                self.mqtt.loop_stop()
                result = self.mqtt.disconnect()
                self.logger.debug(f"Disconnect result: {result}")
        except:
            self.logger.exception("Exception while disconnecting from MQTT - ignoring")

    def loop(self):  # pragma: no cover
        """
        No actual threading for Camera
        No coverage because
        """
        self.logger.debug("Starting MQTT loop")
        try:
            while self.running:
                pass
        except KeyboardInterrupt:
            self.logger.debug("KeyboardInterrupt, ignoring")
        finally:
            self.stop()

    def on_connect(self, client, userdata, flags, rc):
        """
        Event handler for MQTT connection
        """
        self.logger.info(f"mqtt: (CONNECT) client {client._client_id} received with code {rc}")

        # Check the connection results
        if rc != 0:  # pragma: no cover
            message = get_mqtt_error_message(rc)
            self.logger.error(message)
            raise MQTTError(f"on_connect 'rc' failure - {message}")

        # Nothing wrong with RC - subscribe to topic
        self.logger.info("Connection successful")
        # Subscribe to all topics simultaneously
        self.mqtt.subscribe([(x.name, 2) for x in self.config.mqtt_topic])

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

        if self.should_toggle_from_command(msg.topic, message_data):
            thread = Thread(target=self.toggle_loop)
            thread.start()

    def should_toggle_from_command(self, message_topic, message_data) -> bool:
        """
        Check if the message indicates a capture command
        @param message_topic: topic message came from
        @type message_topic: str
        @param message_data: message data as dict
        @type message_data: dict
        @return: whether or not to capture
        @rtype: bool or str
        """
        topic = self.config.mqtt_config.topics_subscribe.get(message_topic)
        if not topic:
            return False

        # has_toggled = False
        # if self.db_enabled:
        #     latest_timestamp = self.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
        #     if latest_timestamp is not None:
        #         last_entry = self.db.get_record(latest_timestamp)
        #         has_toggled = bool(last_entry[DatabaseKeys.TOGGLED])

        command = message_data.get(PubSubKeys.CONTROL)
        if command == GPIODriverCommands.TOGGLE:
            self.logger.info("Received toggle command")
            return True

        self.logger.debug(f"Not toggling for latest message: {message_topic} - {message_data}")
        return False

    # def update_database_entry(self):
    #     """
    #     Update the latest database entry to indicate capturing has happened
    #     """
    #     if self.db_enabled:
    #         latest_timestamp = self.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
    #         if latest_timestamp is not None:
    #             self.db.update_record(latest_timestamp, DatabaseKeys.TOGGLED, int(True))

    def toggle_loop(self):
        """
        Toggle the GPIO
        """
        self.sensor.toggle()

    def cleanup(self):
        """
        Gracefully exit
        """
        super().cleanup()

    def __repr__(self) -> str:
        """
        @rtype: str
        """
        return f"{self.__class__}|{self.config.__class__}|{self.config.mqtt_config.client_id}"