"""
Controller for MQTT environment sensors
Collects data from sensors publishing data on MQTT topics
instead of reading sensors connected to the RPi directly
"""

import json
from threading import Thread
import time
import datetime

from library.communication.mqtt import get_mqtt_error_message, MQTTError
from library.controllers import BaseController, get_logger


class MqttEnvironmentController(BaseController):
    """
    Simple controller that subscribes to MQTT topics and
    stores data received into a database
    """
    def __init__(self, config, debug=False):
        super().__init__(config, debug)

        self.logger = get_logger(__name__, debug, config.log)

        self.thread = Thread(target=self.loop)

    def setup(self):
        """
        Setup MQTT stuff
        """
        if not self.mqtt:
            self.logger.warning("No MQTT client defined! Nothing for MqttEnvironmentController to subscribe to")
            return

        self.logger.debug(f"MQTT Config: {self.mqtt}")
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_message = self.on_message

        self.logger.debug("Connecting MQTT")
        result = self.mqtt.connect()
        self.logger.debug(f"Connection result: {result}")
        self.mqtt.loop_start()

    def start(self):
        """
        No actual threading, just subscribe to MQTT stuff
        """
        self.logger.debug("Starting Camera MQTT connection")
        super().start()
        self.setup()
        self.thread.start()

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down environment MQTT connection")
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

        try:
            # write to database
            with self.db as db:
                timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                temperature = message_data.get('temperature')
                humidity = message_data.get('humidity')

                formatted = f"{msg.topic} @ {timestamp}: {temperature}f, {humidity}%"
                self.logger.info(formatted)

                # do not write if ID is not unique - could be a retained message
                db.add_data([timestamp, msg.topic, temperature, humidity])
        except Exception as e:
            # it's possible for on_message to fire for two messages nearly simultaneously
            # and wind up with the same timestamp, which is the DBs primary key.
            # this could crash the thread
            # just catch it and log it to prevent crashes
            self.logger.exception(str(e))

    # endregion MQTT

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

