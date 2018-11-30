"""
Simple door monitoring controller with PiCamera and MQTT support
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from threading import Thread
import timeit

from library.controllers import BaseController
from library.communication.mqtt import MQTTClient
from library.sensors.gpio_monitor import GPIO_Monitor


class DoorMonitorController(BaseController):
    """
    Basic controller with threads for monitoring door state
    and publishing changes via MQTT.
    Also supports PiCamera for snapping photos when the door opens
    Door state changes & photos can be published via Pushbullet, too
    """
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for environment sensing
        @type config: library.config.door_monitor.DoorMonitorConfig
        @param debug: debug flag
        @type debug: bool
        """
        super(DoorMonitorController, self).__init__(config, debug)

        self.sensor = GPIO_Monitor(
            self.config.pin
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
        return "Open" if self.state else "Closed"

    # region Threading

    def start(self):
        """
        Start the thread
        """
        self.logger.info("Starting GPIO monitor thread")
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

    def loop(self):
        """
        Looping method for threading - reads sensor @ desired intervals and publishes results
        """
        lasttime = 0
        last_state = self.state
        while self.running:

            # Read at the desired frequency
            now = float(timeit.default_timer())
            if now - lasttime > 1.0:
                lasttime = now

                # Do the readings
                try:
                    self.state = self.sensor.read()
                except:
                    self.logger.exception('Failed to read GPIO!')
                    continue

                # Publish
                if last_state != self.state:
                    self.publish(str(self))
                    last_state = self.state

    # endregion Threading
    # region Communication

    def publish(self, state):
        """
        Broadcast sensor readings
        @param state: door state (Open, Closed)
        @type state: str
        """
        if not self.mqtt:
            return

        for topic in self.config.mqtt_topic:

            payload = topic.payload(state=state)
            self.logger.info(
                "Publishing to %s: %s",
                str(topic),
                payload
            )
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
        super(DoorMonitorController, self).cleanup()
        self.sensor.cleanup()
        self.logger.info("Cleanup complete")
