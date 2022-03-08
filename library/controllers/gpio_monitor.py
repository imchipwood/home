"""
Simple door monitoring controller with PiCamera and MQTT support
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import time
from threading import Thread

from library.data import DatabaseKeys
from library import GarageDoorStates
from library.communication.mqtt import MQTTClient
from library.controllers import BaseController, get_logger
from library.data.database import Database
from library.sensors.gpio_monitor import GPIOMonitor


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
        self._state = self.sensor.read()

    @property
    def state(self) -> bool:
        """
        Current GPIO pin state
        @rtype: bool
        """
        return self._state

    @state.setter
    def state(self, state: bool):
        """
        Set the state
        @param state: new state
        @type state: bool
        """
        last_state = self.state
        self._state = state
        if last_state != state:
            self.publish()

    # region Threading

    def start(self):
        """
        Start the thread
        """
        self.logger.info("Starting GPIO monitor thread")
        super().start()
        self.thread = Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """
        Stop the thread
        """
        self.logger.info("Stopping GPIO monitor thread")
        super().stop()

    def loop(self):
        """
        Loop for monitoring GPIO
        """
        last_time = time.time()
        while self.running:
            current_time = time.time()
            if current_time - last_time > self.sensor.config.period:
                last_time = current_time
                self.state = self.sensor.read()

    # endregion Threading
    # region Communication

    def publish(self):
        """
        Broadcast sensor readings
        """
        if not self.mqtt:
            return

        self.logger.debug(f"{self.config.mqtt_config.client_id} state changed: {self}")

        # Check if the state should be published
        if not self.should_publish():
            return

        convo_id = self.add_entry_to_database()

        # Publish to all topics
        for topic in self.config.mqtt_topic:

            # Convert state to MQTT payload and attempt to publish
            payload = topic.payload(state=str(self), convo_id=convo_id)
            self.logger.info(f"Publishing to {topic}: {payload}")
            try:
                self.mqtt.single(topic=str(topic), payload=payload, qos=2)
                self.logger.debug(f"Published to {topic}")
            except:
                self.logger.exception(f"Failed to publish to topic {topic.name}:\n\t{payload}")
                raise

    def should_publish(self) -> bool:
        """
        Check if the new state should be published
        @rtype: bool
        """
        # Default is to publish
        if not self.config.db_name:
            return True

        # Database exists - check previous state against current
        # and check if previous entry is old
        last_entry = self.get_latest_db_entry()
        if last_entry:
            last_state = last_entry[DatabaseKeys.STATE]
            is_recent = self.is_entry_recent(last_entry, 15)
        else:
            last_state = None
            is_recent = None

        # Only publish if the state changed or the previous reading is old
        state_changed = last_state != str(self)
        should_publish = state_changed or not is_recent
        _is_recent = str(is_recent).rjust(5, " ")
        _state_changed = str(state_changed).rjust(5, " ")
        self.logger.debug(f"Recent: {_is_recent}, State changed: {_state_changed}")

        return should_publish

    def add_entry_to_database(self) -> str:
        """
        Add the current state to the database
        @return: new ID to use for this conversation
        @rtype: str
        """
        convo_id = self.sensor.get_id()

        if self.config.db_name:
            with Database(self.config.db_name, self.config.db_columns, self.config.db_path) as db:
                # Create the entry
                raw_data = {
                    DatabaseKeys.TIMESTAMP: int(time.time()),
                    DatabaseKeys.STATE: str(self),
                    DatabaseKeys.ID: convo_id,
                    DatabaseKeys.CAPTURED: int(False),
                    DatabaseKeys.NOTIFIED: int(False)
                }
                data = db.format_data_for_insertion(**raw_data)
                self.logger.debug(f"Adding data to db: {data}")
                db.add_data(data)
                db.delete_all_except_last_n_records(2)

        return convo_id

    # endregion Communication

    def cleanup(self):
        """
        Shut down the thread
        """
        super().cleanup()
        self.sensor.cleanup()
        self.logger.info("Cleanup complete")

    @staticmethod
    def get_state_as_string(state: bool) -> str:
        """
        Convert state to string
        @param state: state as bool
        @type state: bool
        @return: state as string
        @rtype: str
        """
        return GarageDoorStates.OPEN if state else GarageDoorStates.CLOSED

    def __repr__(self) -> str:
        """
        @rtype: str
        """
        return self.get_state_as_string(self.state)
