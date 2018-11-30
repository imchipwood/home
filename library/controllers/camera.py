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

try:
    from picamera import PiCamera
except:
    logging.warning("Failed to import picamera - using mock")
    from library.mock.mock_picamera import PiCamera

from library.controllers import BaseController
from library.communication.mqtt import MQTTClient, MQTTError


class PiCameraController(PiCamera, BaseController):
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.camera.CameraConfig
        @param debug: debug flag
        @type debug: bool
        """
        super(PiCameraController, self).__init__(config=config, debug=debug)

        # Set up the camera
        self.sensor = PiCamera()
        self.capture_path = None
        self.capture_delay = 0
        self.setup()

        self.mqtt = None
        """@type: MQTTClient"""
        if self.config.mqtt_config:
            self.mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)

    # region Threading

    def start(self):
        """
        Camera won't actually do threading - instead, we'll subscribe to an MQTT topic
        """
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_message = self.on_message
        self.connect_mqtt()

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down camera MQTT connection")
        try:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
        except:
            self.logger.exception("Exception while disconnecting from MQTT - ignoring")

    # endregion Threading
    # region MQTT

    def connect_mqtt(self):
        """
        Simply connect to MQTT
        """
        self.mqtt.connect()
        self.mqtt.loop_start()

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
        self.mqtt.subscribe(str(self.config.mqtt_topic), qos=1)

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
        message_data = json.loads(msg.payload)

        # Check if it indicated a capture
        if self.should_capture_from_command(msg.topic, message_data):
            self.logger.info("Received capture command")
            # If no delay in message, pass in None - this will force camera to use
            # the delay defined in the config
            self.capture(delay=message_data.get("delay", None))

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
            message_val = topic.payload.get(key, None)
            if isinstance(message_val, str):
                return message_val.lower() == val.lower()
            else:
                return message_val == val

        # # Did this come from a door?
        # message = message_data.get("state", "")
        # if message:
        #     return message.lower() == "open"
        # # Nope - was it a direct capture command?
        # message = message_data.get("capture", "")
        # if message:
        #     return message.lower() == "capture"

    # endregion MQTT
    # region Camera

    def setup(self):
        """
        Set up the PiCamera based on settings found in config file
        """
        self.logger.debug("cameraSetup")
        self.rotation = self.config.rotation
        self.brightness = self.config.brightness
        self.contrast = self.config.contrast
        self.resolution = self.config.resolution
        self.capture_path = self.config.capture_path
        self.capture_delay = self.config.delay
        self.iso = self.config.iso

    def capture(self, output=None, format=None, use_video_port=False, resize=None, splitter_port=0, delay=None, **options):
        """
        slight modification on built-in capture function to allow not specifying an output and updating camera ISO
        on the fly based on time of day

        @remark: More info here: http://picamera.readthedocs.io/en/release-1.10/api_camera.html

        @param output: Optional, string path to save image to. Defaults to cameraFile attribute if none provided
        @param format: Optional, format to save image in (jpeg, png, gif, etc.)
        @param use_video_port: Optional, boolean, defaults False. Set to true to use video port instead of camera port if you need rapid capture
        @param resize: Optional, tuple of (width, height) to resize image. defaults to None (no resize)
        @param splitter_port: Optional, boolean, default 0, ignored when use_video_port=False. Defines port of video splitter that image encoder will be attached to
        @param delay: Optional, integer, default None, use to delay the camera picture taking by 'delay' seconds
        @param options: no documentation provided by picamera docs
        """
        # Handle output path
        if not output:
            output = self.capture_path
        if os.path.exists(output):
            os.remove(output)

        # Handle capture delay
        target_delay = 0
        if delay is not None:
            target_delay = delay
        elif self.capture_delay:
            target_delay = self.capture_delay
        if target_delay > 0:
            self.logger.debug("Delaying %f seconds before capture", delay)
            time.sleep(target_delay)

        super(PiCameraController, self).capture(
            output=output,
            format=format,
            use_video_port=use_video_port,
            resize=resize,
            splitter_port=splitter_port,
            **options
        )
        self.logger.debug("Capture complete")

    # endregion Camera

    def cleanup(self):
        """
        Gracefully exit
        """
        super(PiCameraController, self).cleanup()
        try:
            self.logger.debug("Disabling camera")
            self.stop_preview()
            self.close()
            self.logger.debug("Camera disabled")
        except:
            self.logger.exception("Exception while shutting down camera")

    def __repr__(self):
        """
        @rtype: str
        """
        return "{}|{}|{}".format(self.__class__, self.config.type, self.mqtt._client_id)

