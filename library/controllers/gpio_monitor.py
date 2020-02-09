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
        self.state = self.sensor.read()

        if self.config.db_name:
            with Database(self.config.db_name, self.config.db_columns) as db:
                data = [int(time.time()), GarageDoorStates.OPEN if self.state else GarageDoorStates.CLOSED]
                self.logger.debug(f"Adding data to db: {data}")
                db.add_data(data)
                db.delete_all_except_last_n_records(2)

        for topic in self.config.mqtt_topic:
            payload = topic.payload(state=str(self))
            self.logger.info(f'Publishing to {topic}: {payload}')
            try:
                self.mqtt.single(
                    topic=str(topic),
                    payload=payload
                )
            except:
                self.logger.exception("Failed to publish MQTT data!")
                raise

    # endregion Communication

    def cleanup(self):
        """
        Shut down the thread
        """
        super().cleanup()
        self.sensor.cleanup()
        self.logger.info("Cleanup complete")
