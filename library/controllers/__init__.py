import os
from abc import ABC, abstractmethod
import logging

from library import setup_logging


def Get_Logger(name, debug_flag, log_path) -> logging.Logger:
    """
    Get a logging.Logger
    @param name: name of logger
    @type name: str
    @param debug_flag: debug_flag flag to enable
    @type debug_flag: bool
    @param log_path: log file path
    @type log_path: str
    @return: Logger with file have
    @rtype: logging.Logger
    """
    # Set up logging
    logging.getLogger().setLevel(logging.DEBUG)
    if log_path and not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    logger = setup_logging(
        logging.getLogger(name),
        logging_level=debug_flag,
        log_path=log_path
    )
    logger.info("Logger initialized")
    return logger


class BaseController(ABC):
    """Base class for all controllers to extend"""
    def __init__(self, config, debug=False):
        super()

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
