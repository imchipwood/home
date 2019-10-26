"""
Simple Pushbullet controller to relay messages received via MQTT
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import os
import json
from threading import Thread
from time import time, sleep

from library.controllers import BaseController, Get_Logger
from library.communication.mqtt import MQTTClient, MQTTError, Get_MQTT_Error_Message
from library.communication import pushbullet


class PushbulletController(BaseController):
    """
    Basic threaded controller to relay MQTT messages
    """
    def __init__(self, config, debug=False):
        """

        @param config: path to config file
        @type config: library.config.pushbullet.PushbulletConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config, debug)

        self.logger = Get_Logger(__name__, debug, config.log)

        self.mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)
        
    # region Threading

    def start(self):
        """
        Pushbullet won't actually do threading - instead, subscribe to an MQTT topic
        """
        self.logger.debug("Starting Pushbullet MQTT connection")
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_message = self.on_message
        self.connect_mqtt()
        self.running = True

    def loop(self):
        """
        No actual threading for Pushbullet
        """
        try:
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            pass

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down pushbullet MQTT connection")
        try:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
        except:
            self.logger.exception("Exception while disconnecting from MQTT - ignoring")
        self.running = False

    # endregion Threading
    # region MQTT

    def connect_mqtt(self):
        """
        Simply connect to MQTT
        """
        if self.config.mqtt_topic and not self.running:
            self.logger.debug("in connect_mqtt")
            self.mqtt.connect()
            self.thread = Thread(target=self.loop)
            self.thread.daemon = True
            self.thread.start()

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

        topic = self.mqtt.config.topics_subscribe.get(msg.topic)
        if topic:
            state = message_data.get("state")
            notification = self.config.notify.get(state)
            self.logger.debug(f"Received '{state}': {notification}")

            if state == "Open":
                if not self.wait_for_file_refresh(notification):
                    return

                try:
                    pushbullet.PushbulletImageNotify(
                        self.config.api_key,
                        notification
                    )
                except:
                    self.logger.exception("Exception attempting to send Pushbullet image notification")
                    
            elif state == "Closed":
                try:
                    pushbullet.PushbulletTextNotify(
                        self.config.api_key,
                        msg.topic,
                        notification
                    )
                except:
                    self.logger.exception("Exception attempting to send Pushbullet text notification")

    def wait_for_file_refresh(self, file_path):
        """
        Check if a file exists
        @param file_path: path to
        @type file_path: str
        @return: whether or not the file was found
        @rtype: bool
        """
        if os.path.exists(file_path):
            # image exists - wait a couple seconds and then check again to make sure it's the right one
            sleep(2)

        initial_time = time()
        while not os.path.exists(file_path):
            sleep(1)
            if (time() - initial_time) > self.config.max_notification_delay:
                self.logger.error(
                    f"Did not detect image in {self.config.max_notification_delay}"
                    f" - no notification will be sent"
                )
                return False

        return True

    # endregion MQTT

    def cleanup(self):
        """
        Gracefully exit
        """
        super().cleanup()

    def __repr__(self):
        """
        @rtype: str
        """
        return f"{self.__class__}|{self.config.type}|{self.mqtt._client_id}"
