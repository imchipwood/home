import logging
import os
from abc import ABC, abstractmethod
from multiprocessing import Process
from time import time
from typing import List

from library import setup_logging
from library.communication.mqtt import MQTTClient
from library.data.database import Database
from library.data import DatabaseKeys

RUNNING = False


def get_logger(name, debug_flag, log_path) -> logging.Logger:
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

        self._mqtt = None
        self.logger = None
        self.thread = None  # type: Process

    @property
    def running(self) -> bool:
        """
        Check if monitor is running
        @rtype: bool
        """
        global RUNNING
        return RUNNING

    @running.setter
    def running(self, running: bool):
        """
        Set running flag
        @type running: bool
        """
        global RUNNING
        RUNNING = running

    @property
    def mqtt(self) -> MQTTClient:
        """
        Get the MQTTClient
        @rtype: MQTTClient
        """
        if not self._mqtt and self.config.mqtt_config:
            self._mqtt = MQTTClient(mqtt_config=self.config.mqtt_config)
        return self._mqtt

    @abstractmethod
    def start(self):
        """
        Start the thread
        """
        self.running = True

    @abstractmethod
    def stop(self):
        """
        Stop the thread
        """
        self.running = False

    @abstractmethod
    def loop(self):
        """
        Looping method for threading
        """
        pass  # pragma: no cover

    @abstractmethod
    def cleanup(self):
        """
        Stop threads and do any other cleanup required
        """
        self.stop()

    @property
    def db_enabled(self) -> bool:
        """
        Check if a database is available
        @rtype: bool
        """
        return self.config.db_name and self.config.db_columns

    @property
    def db(self) -> Database:
        """
        Get the Database object for this controller
        @rtype: Database
        """
        return Database(self.config.db_name, self.config.db_columns)

    def get_latest_db_entry(self, column_name: str = DatabaseKeys.STATE) -> int or float or str:
        """
        Get the latest value from the database
        @rtype: int or float or str
        """
        latest = None
        if self.config.db_name:
            self.logger.debug(f"Opening DB {self.config.db_name}")
            with self.db as db:
                record = db.get_latest_record()
                if record:
                    latest = record[column_name]
                    self.logger.debug(f"Latest db entry at column {column_name}: {latest}")
        return latest

    def get_last_two_db_entries(self, column_name: str = DatabaseKeys.STATE) -> List:
        """
        Get the last two entries from the DB
        @param column_name: name of column to get
        @type column_name: str
        @return: list of values from last two entries
        @rtype: list
        """
        entries = []
        if self.config.db_name:
            self.logger.debug(f"Opening DB {self.config.db_name}")
            with self.db as db:
                records = db.get_last_n_records(2)
                if len(records) == 2:
                    entries = [record[column_name] for record in records]
                    self.logger.debug(f"Latest db entry at column {column_name}: {entries}")
        return entries

    def is_latest_entry_recent(self, delta_time: int = 60) -> bool:
        """
        Check if the latest database entry is 'recent'
        @param delta_time: amount of time to be considered 'recent'
        @type delta_time: int
        @return: whether the latest entry is 'recent' or not
        @rtype: bool
        """
        latest = self.get_latest_db_entry(DatabaseKeys.TIMESTAMP)
        if latest is None:
            # No recent entry
            return True

        return time() - latest < delta_time
