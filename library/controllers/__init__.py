from abc import ABC, abstractmethod
import logging

from library import setup_logging


def Get_Logger(name, debug, path):
    # Set up logging
    logging.getLogger().setLevel(logging.DEBUG)
    logger = setup_logging(
        logging.getLogger(name),
        logging_level=debug,
        log_path=path
    )
    logger.info("Logger initialized")
    return logger


class BaseController(ABC):
    """Base class for all controllers to extend"""
    def __init__(self, config, debug=False):
        super(BaseController, self).__init__()

        self.debug = debug
        self.config = config

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
        self.stop()
