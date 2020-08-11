"""
Camera Controller
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
from threading import Thread, Lock

from library.communication.mqtt import MQTTError, get_mqtt_error_message
from library.config import PubSubKeys
from library.config.camera import ConfigKeys
from library.controllers import BaseController, get_logger
from library.data import DatabaseKeys
from library.sensors.camera import Camera

mutex = Lock()


class PiCameraController(BaseController):
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.camera.CameraConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config=config, debug=debug)

        self.logger = get_logger(__name__, debug, config.log)

        self.thread = Thread(target=self.loop)

    # region Threading

    def setup(self):
        """
        Setup MQTT stuff
        """
        if not self.mqtt:
            self.logger.warning("No MQTT client defined! Nothing for camera controller to do.")
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
        self.logger.debug("Starting Camera MQTT connection")
        super().start()
        self.setup()
        self.thread.start()

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down camera MQTT connection")
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

    # endregion Threading
    # region MQTT

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

        # Check if it indicated a capture
        should_capture = self.should_capture_from_command(msg.topic, message_data)
        if should_capture is not False:
            # If no delay in message, pass in None - this will force camera to use
            # the delay defined in the config
            kwargs = {
                ConfigKeys.DELAY: message_data.get(ConfigKeys.DELAY, None),
                PubSubKeys.FORCE: message_data.get(
                    PubSubKeys.FORCE,
                    True if should_capture == PubSubKeys.FORCE else False
                )
            }
            thread = Thread(target=self.capture_loop, kwargs=kwargs)
            thread.start()

    def should_capture_from_command(self, message_topic, message_data) -> bool or str:
        """
        Check if the message indicates a capture command
        @param message_topic: topic message came from
        @type message_topic: str
        @param message_data: message data as dict
        @type message_data: dict
        @return: whether or not to capture
        @rtype: bool or str
        """
        # Check all the topics we're subscribed to
        topic = self.config.mqtt_config.topics_subscribe.get(message_topic)
        if not topic:
            return False

        # Check the database to see if capturing already occurred for latest entry
        has_captured = False
        if self.db_enabled:
            latest_timestamp = self.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
            if latest_timestamp is not None:
                last_entry = self.db.get_record(latest_timestamp)
                has_captured = bool(last_entry[DatabaseKeys.CAPTURED])
                self.logger.info(f"Latest db entry: {has_captured}")

        # Check
        if message_data.get(PubSubKeys.CAPTURE):
            self.logger.info("Received direct capture command")
            return PubSubKeys.FORCE

        # Check the payload - assumes a single value
        for key, val in message_data.items():
            if key != PubSubKeys.STATE:
                # Ignore non-state keys - they are handled elsewhere
                continue

            message_val = topic.payload().get(key, None)

            if isinstance(message_val, str):
                message_val = message_val.lower()
                val = val.lower()

            # Capture if message matches
            should_capture = message_val == val

            # Don't capture if latest DB entry has already been captured
            if self.db_enabled:
                should_capture &= not has_captured

            # Return now if should_capture is True
            if should_capture:
                self.logger.info("Received message indicating capture")
                return should_capture

        # Not capturing
        self.logger.debug(f"Not capturing for latest message: {message_topic} - {message_data}")
        return False

    def publish(self, force=False):
        """
        Broadcast that an image was taken
        @param force: whether or not to force publishing of the image
        @type force: bool
        """
        if not self.mqtt:
            return

        for name, topic in self.config.mqtt_config.topics_publish.items():
            if PubSubKeys.FORCE in topic.raw_payload:
                raw_payload = topic.raw_payload
                force_publish = True if force else False
                raw_payload[PubSubKeys.FORCE] = force_publish
                payload = topic.payload(**raw_payload)
            else:
                payload = topic.raw_payload

            self.logger.info(f"Publish to {name}: {topic.raw_payload}")
            self.mqtt.single(str(topic), payload=payload, retain=False, qos=2)

    def update_database_entry(self):
        """
        Update the latest database entry to indicate capturing has happened
        """
        if not self.db_enabled:
            return

        latest_timestamp = self.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
        if latest_timestamp is not None:
            self.db.update_record(latest_timestamp, DatabaseKeys.CAPTURED, int(True))

    # endregion MQTT
    # region Camera

    def capture_loop(self, delay=0, force=False):
        """
        Simple method for capturing an image with PiCamera
        """
        with mutex, Camera(self.config, self.debug) as camera:
            camera.capture(delay=delay)
            self.publish(force=force)
            self.update_database_entry()

    # endregion Camera

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
