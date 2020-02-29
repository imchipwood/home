"""
Simple door monitoring controller with PiCamera and MQTT support
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import time
from threading import Thread

from library import GarageDoorStates
from library.communication.mqtt import MQTTClient
from library.controllers import BaseController, get_logger
from library.data.database import Database
from library.sensors.gpio_monitor import GPIOMonitor, GPIO


class GPIOMonitorController(BaseController):
    """
    Basic controller with threads for monitoring GPIO state
    and publishing changes via MQTT.
    """

    def __init__(self, config, debug=False):
        """
        @param config: configuration object for GPIO monitoring
        @type config: library.config.gpio_monitor.GPIOMonitorConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config, debug)

        self.logger = get_logger(__name__, debug, config.log)

        self.sensor = GPIOMonitor(
            self.config,
            debug=debug
        )
        self.state = self.sensor.read()

        # Set up MQTT
        self.mqtt = None
        """@type: MQTTClient"""
        if self.config.mqtt_config:
            self.mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)

    def __repr__(self):
        """
        @rtype: str
        """
        return GarageDoorStates.OPEN if self.state else GarageDoorStates.CLOSED

    # region Threading

    def start(self):
        """
        Start the thread
        """
        self.logger.info("Starting GPIO monitor thread")
        self.sensor.add_event_detect(GPIO.BOTH, self.publish_event)
        self.thread = Thread(target=self.loop)
        self.thread.daemon = True
        self.running = True
        self.thread.start()

    def stop(self):
        """
        Stop the thread
        """
        self.logger.info("Stopping GPIO monitor thread")
        self.running = False
        self.sensor.remove_event_detect()

    def loop(self):
        while self.running:
            pass

    # endregion Threading
    # region Communication

    def publish_event(self, channel):
        """
        Broadcast sensor readings
        @param channel: GPIO pin event fired on
        @type channel: int
        """
        if not self.mqtt:
            return

        # Update the current state
        self.state = self.sensor.read()

        # Check if the state should be published
        if self.should_publish():

            self.add_entry_to_database()

            # Publish to all topics
            for topic in self.config.mqtt_topic:

                # Convert state to MQTT payload and attempt to publish
                payload = topic.payload(state=str(self))
                self.logger.info(f'Publishing to {topic}: {payload}')
                try:
                    self.mqtt.single(topic=str(topic), payload=payload)
                except:
                    self.logger.exception(f"Failed to publish to topic {topic.name}:\n\t{payload}")
                    raise

    def should_publish(self) -> bool:
        """
        Check if the new state should be published
        @rtype: bool
        """
        # Default is to publish
        shouldPublish = True

        if self.config.db_name:
            # Database exists - check previous state against current
            # and check if previous entry is old
            lastState = self.get_latest_db_entry()
            isRecent = self.is_latest_entry_recent(3)

            # Only publish if the state changed or the previous reading is old
            shouldPublish = lastState != str(self.state) or not isRecent

        return shouldPublish

    def add_entry_to_database(self):
        """
        Add the current state to the database
        """
        if self.config.db_name:
            with Database(self.config.db_name, self.config.db_columns) as db:
                # Create the entry
                data = [int(time.time()), str(self.state)]
                self.logger.debug(f"Adding data to db: {data}")
                db.add_data(data)
                db.delete_all_except_last_n_records(2)

    # endregion Communication

    def cleanup(self):
        """
        Shut down the thread
        """
        super().cleanup()
        self.sensor.cleanup()
        self.logger.info("Cleanup complete")
