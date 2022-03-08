
import time
from threading import Thread

from library import GarageDoorStates
from library.controllers import BaseController, get_logger
from library.data.database import Database

if False:
    from library.config.timer import TimerConfig


class TimerController(BaseController):

    def __init__(self, config, debug=False):
        """

        @param config:
        @type config: TimerConfig
        @param debug:
        @type debug:
        """
        super().__init__(config, debug)

        self.config = config  # type: TimerConfig

        self.logger = get_logger(__name__, debug, config.log)

    def start(self):
        self.logger.info("Starting timer thread")
        super().start()
        self.thread = Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.logger.info("Stopping timer thread")
        super().stop()

    def cleanup(self):
        """
        Stop threads and do any other cleanup required
        """
        self.stop()

    def loop(self):
        last_time = time.time()
        while self.running:
            current_time = time.time()
            if current_time - last_time > self.config.period:
                last_time = current_time
                self.publish()

    def publish(self):
        if not self.mqtt:
            return
        self.logger.debug(f"{self.config.mqtt_config.client_id} publishing")

        self.add_entry_to_database()

        for topic in self.config.mqtt_topic:

            payload = topic.payload(**topic.raw_payload)
            self.logger.info(f"Publishing to {topic}: {payload}")

            try:
                self.mqtt.single(topic=str(topic), payload=payload, qos=2)
                self.logger.debug(f"published to {topic}")
            except:
                self.logger.exception(f"Failed to publish to topic {topic.name}:\n\t{payload}")
                raise

    def add_entry_to_database(self):
        """
        Add the current state to the database
        """
        if not self.config.db_name:
            return

        with Database(self.config.db_name, self.config.db_columns, self.config.db_path) as db:
            # Create the entry
            data = [int(time.time()), GarageDoorStates.OPEN, int(False), int(False)]
            self.logger.debug(f"Adding data to db: {data}")
            db.add_data(data)
            db.delete_all_except_last_n_records(2)
