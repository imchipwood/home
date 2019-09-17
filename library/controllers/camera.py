"""
Camera Controller
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging
import time
import os
import json
from multiprocessing import Process
from threading import Thread

from library.sensors.camera import Camera

from library.controllers import BaseController
from library.communication.mqtt import MQTTClient, MQTTError


# class PiCameraController(PiCamera, BaseController):
class PiCameraController(BaseController):
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.camera.CameraConfig
        @param debug: debug flag
        @type debug: bool
        """
        # PiCamera.__init__(self)
        # BaseController.__init__(self, config=config, debug=debug)
        super(PiCameraController, self).__init__(config=config, debug=debug)

        # Set up the camera
        # self.camera = Camera(config, debug)

        self.mqtt = None
        """@type: MQTTClient"""
        if self.config.mqtt_config:
            self.mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)

    # region Threading

    def start(self):
        """
        Camera won't actually do threading - instead, we'll subscribe to an MQTT topic
        """
        self.logger.debug("Starting Camera MQTT connection")
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_message = self.on_message
        self.connect_mqtt()
        self.running = True

    def loop(self):
        """
        No actual threading for Camera
        """
        try:
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            pass

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down camera MQTT connection")
        try:
            self.thread.terminate()
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
            self.thread = Process(target=self.loop)
            self.thread.start()

    def on_connect(self, client, userdata, flags, rc):
        """
        Event handler for MQTT connection
        """
        self.logger.info("mqtt: (CONNECT) client %s received with code %d", client._client_id, rc)

        # Check the connection results
        if rc != 0:
            # Something bad happened
            message = "Error: rc={}, ".format(rc)
            if rc == -4:
                message += "Too many messages"
            elif rc == -5:
                message += "Invalid UTF-8 string"
            elif rc == -9:
                message += "Bad QoS"

            self.logger.error(message)
            raise MQTTError("on_connect 'rc' failure - {}".format(message))

        # Nothing wrong with RC - subscribe to topic
        self.logger.info("Connection successful")
        # Subscribe to all topics simultaneously
        self.mqtt.subscribe([(x.name, 1) for x in self.config.mqtt_topic])

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """
        Simply log subscription status
        """
        self.logger.debug("mqtt: (SUBSCRIBE) client: %s, mid %s, granted_qos: %s", client._client_id, mid, granted_qos)

    def on_message(self, client, userdata, msg):
        """
        Handler for new MQTT message
        """
        self.logger.debug(
            "mqtt: (MESSAGE) client: %s, topic: %s, QOS: %d, payload: %s",
            client._client_id,
            msg.topic,
            msg.qos,
            msg.payload
        )

        # Convert message to JSON
        payload = msg.payload.decode("utf-8")
        self.logger.debug("received payload: %s", payload)
        try:
            message_data = json.loads(payload)
        except ValueError as e:
            self.logger.warning("Some error while converting string payload to dict: %s", e)
            return

        # Check if it indicated a capture
        if self.should_capture_from_command(msg.topic, message_data):
            self.logger.info("Received capture command")
            # If no delay in message, pass in None - this will force camera to use
            # the delay defined in the config
            kwargs = {"delay": message_data.get("delay", None)}
            thread = Thread(target=self.capture_loop, kwargs=kwargs)
            thread.start()

    def should_capture_from_command(self, message_topic, message_data):
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

        # Check the payload - assumes a single value
        for key, val in message_data.items():
            if key == "delay":
                continue
            message_val = topic.payload().get(key, None)
            if isinstance(message_val, str):
                return message_val.lower() == val.lower()
            else:
                return message_val == val

        # Shouldn't ever get here but just in case...
        self.logger.warning("Didn't find expected payload - not capturing!")
        return False

    # endregion MQTT
    # region Camera

    def capture_loop(self, delay=0):
        with Camera(self.config, self.debug) as camera:
            camera.capture(delay=delay)

    # endregion Camera

    def cleanup(self):
        """
        Gracefully exit
        """
        super(PiCameraController, self).cleanup()

    def __repr__(self):
        """
        @rtype: str
        """
        return "{}|{}|{}".format(self.__class__, self.config.type, self.mqtt._client_id)
