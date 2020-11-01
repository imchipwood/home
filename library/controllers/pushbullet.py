"""
Simple Pushbullet controller to relay messages received via MQTT
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import json
from threading import Thread
from time import time

from urllib3.exceptions import MaxRetryError

from library import GarageDoorStates
from library.communication.mqtt import MQTTError, get_mqtt_error_message
from library.communication.pushbullet import PushBulletNotify
from library.config import PubSubKeys
from library.controllers import BaseController, get_logger
from library.data import DatabaseKeys


class PushBulletController(BaseController):
    """
    Basic threaded controller to relay MQTT messages
    """

    RECENT_ENTRY_THRESHOLD = 5 * 60

    def __init__(self, config, debug=False):
        """

        @param config: path to config file
        @type config: library.config.pushbullet.PushbulletConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config, debug)

        self.logger = get_logger(__name__, debug, config.log)
        try:
            self.notifier = PushBulletNotify(self.config.api_key)
        except MaxRetryError:
            self.logger.exception("Failed to connect to PushBullet")
            self.notifier = None

    # region Threading

    def start(self):
        """
        Pushbullet won't actually do threading - instead, subscribe to an MQTT topic
        """
        self.logger.debug("Starting PushBullet MQTT connection")
        super().start()
        self.mqtt.on_message = self.on_message
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_connect = self.on_connect

        if not self.config.mqtt_topic:
            return

        self.mqtt.connect()
        self.thread = Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """
        Disconnect from MQTT
        """
        self.logger.info("Shutting down PushBullet MQTT connection")
        super().stop()
        try:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
        except:
            self.logger.exception("Exception while disconnecting from MQTT - ignoring")

    def loop(self):
        """
        No actual threading for PushBullet
        """
        try:
            self.mqtt.loop_forever()
        except KeyboardInterrupt:
            pass

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
        topics = [x.name for x in self.config.mqtt_topic]
        self.logger.info(f"Connection successful - subscribing to {topics}")
        # Subscribe to all topics simultaneously
        self.mqtt.subscribe([(x, 2) for x in topics])

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
        if not topic:
            return

        state = message_data.get(PubSubKeys.STATE)
        force = message_data.get(PubSubKeys.FORCE, False)
        convo_id = message_data.get(PubSubKeys.ID)
        notification = self.config.notify.get(state)
        self.logger.debug(f"From {convo_id} - '{state}': {notification}")

        if not self.notifier:  # pragma: no cover
            self.logger.warning("No PushBullet connection - trying again")
            try:
                self.notifier = PushBulletNotify(self.config.api_key)
            except MaxRetryError:
                return

        if state == GarageDoorStates.CLOSED:
            # Message from GPIO monitor saying CLOSED
            if self.db_enabled and not self.should_text_notify(convo_id=convo_id):  # pragma: no cover
                self.logger.debug(f"Latest state '{state}' has not changed recently - will not send notification")
                return
            try:
                self.logger.debug(f"Sending text notification for state {state} from id {convo_id}")
                self.notifier.send_text(msg.topic, notification)
                self.mark_entry_notified(convo_id=convo_id, state=state)
            except:
                self.logger.exception("Exception attempting to send PushBullet text notification")

        elif state == PubSubKeys.PUBLISH:
            # Message is from camera saying to publish the image
            if not self.should_image_notify(force=force, convo_id=convo_id):
                self.logger.debug(f"Received image publish command but already published - not publishing")
                return
            try:
                self.logger.debug(f"Sending image notification for state {state} from id {convo_id}")
                self.notifier.send_file(notification)
                if not force:
                    # Force means camera received direct capture command - no DB entry to update
                    self.mark_entry_notified(convo_id=convo_id, state=state)
            except:
                self.logger.exception("Exception attempting to send PushBullet image notification")

    def mark_entry_notified(self, convo_id: str, state: str):
        """
        Mark the latest entry as "notified"
        @param convo_id: target entry ID
        @type convo_id: str
        @param state: state in case no entry found
        @type state: str
        """
        if not self.db_enabled:
            return

        target_entry = self.get_entry_for_id(convo_id)
        notified = int(True)
        if target_entry:
            timestamp = target_entry[DatabaseKeys.TIMESTAMP]
            self.logger.debug(f"Updating DB entry for id '{convo_id}': {DatabaseKeys.NOTIFIED} = True")
            self.db.update_record(timestamp, DatabaseKeys.NOTIFIED, notified)

        else:
            timestamp = int(time())
            state_to_log = state
            if state != GarageDoorStates.CLOSED:
                state_to_log = GarageDoorStates.OPEN
            raw_data = {
                DatabaseKeys.TIMESTAMP: timestamp,
                DatabaseKeys.STATE: state_to_log,
                DatabaseKeys.ID: convo_id,
                DatabaseKeys.CAPTURED: int(True),
                DatabaseKeys.NOTIFIED: notified
            }
            data = self.db.format_data_for_insertion(**raw_data)
            self.logger.debug(f"Didn't find DB entry for id '{convo_id}' - adding {data}")
            self.db.add_data(data)

    def should_text_notify(self, convo_id: str) -> bool:
        """
        Check if a text notification should be sent
        @param convo_id: conversation ID
        @type convo_id: str
        @rtype: bool
        """
        # Check if entry for ID exists
        target_entry = self.get_entry_for_id(convo_id)
        if target_entry:
            if target_entry[DatabaseKeys.NOTIFIED] \
                    or target_entry[DatabaseKeys.STATE] == GarageDoorStates.OPEN:
                # Already notified or wrong state - don't notify
                return False

        # No entry for this ID - publish!
        return True

    def should_image_notify(self, convo_id: str, force: bool = False) -> bool:
        """
        Check if an image notification should be sent
        @rtype: bool
        """
        # If force, must publish
        if force:
            return True

        # If no DB, no way to check if notification has already been sent
        if not self.db_enabled:
            return True

        # Check if ID matches existing record
        target_entry = self.get_entry_for_id(convo_id)
        if target_entry:
            if target_entry[DatabaseKeys.NOTIFIED] \
                    or target_entry[DatabaseKeys.STATE] == GarageDoorStates.CLOSED:
                # Already notified or wrong state - don't notify
                return False

        # No entry for this ID - publish!
        return True

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
        return f"{self.__class__}|{self.config.__class__}|{self.mqtt._client_id}"
