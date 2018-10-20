from abc import ABC, abstractmethod
import logging

from library import setup_logging


class Controller(ABC):
	"""Base class for all controllers to extend"""
	def __init__(self, config, debug=False):
		super(Controller, self).__init__()

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

		self.running = False
		self.thread = None

	@abstractmethod
	def start(self):
		"""
		Start the thread
		"""
		pass

	@abstractmethod
	def stop(self):
		"""
		Stop the thread
		"""
		pass

	@abstractmethod
	def loop(self):
		"""
		Looping method for threading
		"""
		pass

	@abstractmethod
	def cleanup(self):
		"""
		Stop threads and do any other cleanup required
		"""
		pass