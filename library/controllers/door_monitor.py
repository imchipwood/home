from threading import Thread
import timeit

from library.controllers import BaseController
from library.communication.mqtt import MQTTClient


class DoorMonitorController(BaseController):
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for environment sensing
        @type config: library.config.door_monitor.DoorMonitorConfig
        @param debug: debug flag
        @type debug: bool
        """
        super(DoorMonitorController, self).__init__(config, debug)

        # Set up MQTT
        self.mqtt = None
        """@type: MQTTClient"""
        if self.config.mqtt_config:
            self.mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)

    # region Threading

    def start(self):
        """
        Start the thread
        """
        self.logger.info("Starting environment thread")
        self.thread = Thread(target=self.loop)
        self.thread.daemon = True
        self.running = True
        self.thread.start()

    def stop(self):
        """
        Stop the thread
        """
        self.logger.info("Stopping environment thread")
        self.running = False

    def loop(self):
        """
        Looping method for threading - reads sensor @ desired intervals and publishes results
        """
        lasttime = 0
        # while self.running:
        #
        #     # Read at the desired frequency
        #     now = float(timeit.default_timer())
        #     if now - lasttime > self.config.period:
        #         lasttime = now
        #
        #         # Do the readings
        #         try:
        #             humidity, temperature = self.sensor.read_n_times(5)
        #         except:
        #             self.logger.exception('Failed to read environment sensor!')
        #             continue
        #
        #         # Publish
        #         self.publish(humidity, temperature, self.sensor.units)

    # endregion Threading
    # region Communication

    def publish(self, state):
        """
        Broadcast environment readings
        @param state: door state (Open, Closed)
        @type state: str
        """
        if not self.mqtt:
            return

        self.logger.info("Publishing to {}: {}".format(
            self.config.mqtt_topic,
            state)
        )
        try:
            self.mqtt.single(
                topic=self.config.mqtt_topic,
                payload=state
            )
        except:
            self.logger.exception("Failed to publish MQTT data!")

    # endregion Communication

    def cleanup(self):
        """
        Shut down the thread
        """
        super(DoorMonitorController, self).cleanup()
        self.logger.info("Cleanup complete")

    # def __repr__(self):
    #     """
    #     @rtype: str
    #     """
    #     return "{}|{}|{}".format(self.__class__, self.config.type, self.config.pin)