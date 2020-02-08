"""
Controller for environment sensors
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
from threading import Thread
import timeit
import json

from library.controllers import BaseController, Get_Logger
from library.communication.mqtt import MQTTClient
from library.sensors import SensorError
from library.sensors.environment import EnvironmentSensor


class EnvironmentController(BaseController):
    """
    Simple controller with threads for reading environment sensors
    and publishing data via MQTT
    """
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for environment sensing
        @type config: library.config.environment.EnvironmentConfig
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config, debug)

        self.logger = Get_Logger(__name__, debug, config.log)

        # Set up the sensor
        self.sensor = EnvironmentSensor(
            config=self.config,
            debug=self.debug
        )

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
        while self.running:

            # Read at the desired frequency
            now = float(timeit.default_timer())
            if now - lasttime > self.config.period:
                lasttime = now

                # Do the readings
                try:
                    humidity, temperature = self.sensor.read_n_times(5)
                except SensorError as e:
                    self.logger.error(str(e))
                    continue
                except:
                    self.logger.exception("Some error while reading sensor")
                    continue

                # Publish
                self.publish(humidity, temperature, self.sensor.units)

    # endregion Threading
    # region Communication

    def publish(self, humidity, temperature, units):
        """
        Broadcast environment readings
        @param humidity: humidity %
        @type humidity: float
        @param temperature: temperature
        @type temperature: float
        @param units: temperature units
        @type units: str
        """
        if not self.mqtt:
            return

        for topic in self.config.mqtt_topic:
            payload = topic.payload(
                temperature=temperature,
                humidity=humidity,
                units=units
            )

            self.logger.info(f'Publishing to {topic}: {json.dumps(payload, indent=2)}')
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
        self.logger.info("Cleanup complete")

    def __repr__(self):
        """
        @rtype: str
        """
        return f"{self.__class__}|{self.config.type}|{self.config.pin}"
