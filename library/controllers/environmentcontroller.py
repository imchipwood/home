import logging
from threading import Thread
import timeit
import time
import json

from library import setup_logging
from library.communication.mqtt import MQTTClient
from library.sensors.sensor_environment import EnvironmentSensor


class EnvironmentController(object):
	def __init__(self, config, debug=False):
		"""
		@param config: configuration object for environment sensing
		@type config: library.config.environmentconfig.EnvironmentConfig
		@param debug: debug flag
		@type debug: bool
		"""
		super(EnvironmentController, self).__init__()
		self.debug = debug
		self.config = config

		# Set up logging
		logging.getLogger().setLevel(logging.DEBUG)
		self.logger = setup_logging(
			logging.getLogger(__name__),
			loggingLevel=self.debug,
			logFile=self.config.log
		)
		self.logger.info("Logger initialized")

		# Set up the sensor
		self.sensor = EnvironmentSensor(
			sensorType=self.config.type,
			pin=self.config.pin,
			units=self.config.units,
			debug=self.debug
		)

		# Set up MQTT
		self.mqtt = None
		"""@type: MQTTClient"""
		if self.config.mqttconfig:
			self.mqtt = MQTTClient(mqttconfig=self.config.mqttconfig)

		# Set up the thread
		self.running = False
		self.thread = Thread(target=self.loop, args=[])

	def start(self):
		"""
		Start the thread
		"""
		self.logger.info("Starting environment thread")
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
		Looping method for threading
		"""
		lasttime = 0
		while self.running:
			now = float(timeit.default_timer())

			# Adhere to the reading frequency
			if now - lasttime > self.config.period:
				lasttime = now

				# Do the readings
				try:
					temperature, humidity = self.sensor.readntimes(5)
				except:
					self.logger.exception('Failed to read environment sensor!')
					continue

				# Publish
				if self.mqtt:
					payload = {
						'temperature': "{:0.1f}".format(temperature),
						'humidity': "{:0.1f}".format(humidity)
					}
					self.logger.info("Publishing to {}: {}".format(
						self.config.mqtttopic,
						json.dumps(payload, indent=2))
					)
					try:
						self.mqtt.single(
							topic=self.config.mqtttopic,
							payload=payload
						)
					except:
						self.logger.exception("Failed to publish MQTT data!")

			else:
				# Haven't waited long enough - sleep for a bit
				time.sleep(10)

	def cleanup(self):
		"""
		Do nothing - just a standard method placeholder
		"""
		self.logger.info("Stopping environment thread...")
		self.running = False
		self.logger.info("Cleanup complete")
