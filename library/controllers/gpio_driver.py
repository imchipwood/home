"""
Simple gpio driver controller with MQTT support
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
import logging
from threading import Thread

from library import GPIODriverCommands
from library.communication.mqtt import get_mqtt_error_message, MQTTError
from library.config import PubSubKeys
from library.controllers import BaseController, get_logger
from library.sensors.gpio_driver import GPIODriver

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError, ModuleNotFoundError):  # pragma: no cover
    from library.sensors import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Failed to import RPi.GPIO - using mock library")
    from library.mock.mock_gpio import GPIO

if False:
    from library.config.gpio_driver import GPIODriverConfig


class GPIODriverController(BaseController):

    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.gpio_driver.GPIODriverConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config, debug)

        self.config = config  # type: GPIODriverConfig

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

        self.sensor.initialize()

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
            if not self.mqtt:
                return

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

        command = self.get_gpio_command_from_message(msg.topic, message_data)
        if command == GPIODriverCommands.TOGGLE:
            thread = Thread(target=self.toggle_loop)
            thread.start()
        elif command == GPIODriverCommands.ON:
            thread = Thread(target=self.gpio_on_loop)
            thread.start()
        elif command == GPIODriverCommands.OFF:
            thread = Thread(target=self.gpio_off_loop)
            thread.start()

    def get_gpio_command_from_message(self, message_topic, message_data) -> str or None:
        """
        Check if the message indicates a capture command
        @param message_topic: topic message came from
        @type message_topic: str
        @param message_data: message data as dict
        @type message_data: dict
        @return: whether or not to capture
        """
        topic = self.config.mqtt_config.topics_subscribe.get(message_topic)
        if not topic:
            return None

        command = message_data.get(PubSubKeys.CONTROL)
        if command in [GPIODriverCommands.TOGGLE, GPIODriverCommands.ON, GPIODriverCommands.OFF]:
            self.logger.info(f"Received command: {command}")
            return command

        self.logger.debug(f"Not toggling for latest message: {message_topic} - {message_data}")
        return None

    def toggle_loop(self):
        """
        Toggle the GPIO
        """
        self.sensor.toggle()

    def gpio_on_loop(self):
        """
        Set GPIO to ON
        """
        self.sensor.write_on()

    def gpio_off_loop(self):
        """
        Set GPIO to OFF
        """
        self.sensor.write_off()

    def cleanup(self):
        """
        Gracefully exit
        """
        super().cleanup()
        self.sensor.cleanup()
        self.logger.info("Cleanup complete")

    def __repr__(self) -> str:
        """
        @rtype: str
        """
        return f"{self.__class__}|{self.config.__class__}|{self.config.mqtt_config.client_id}"
