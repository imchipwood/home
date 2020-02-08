import os
from time import time
from abc import ABC, abstractmethod
import logging
from typing import List

from library import setup_logging, GarageDoorStates
from library.data.database import Database


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

        self.logger = None
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

    def get_latest_db_entry(self, column_name: str = 'state'):
        """
        Get the latest value from the database
        @return:
        @rtype: int or float or str
        """
        latest = None
        if self.config.db_name:
            self.logger.debug(f"Opening DB {self.config.db_name}")
            with Database(self.config.db_name, self.config.db_columns) as db:
                record = db.get_latest_record()
                if record:
                    latest = record[column_name]
                    self.logger.debug(f"Latest db entry at column {column_name}: {latest}")
        return latest

    def get_last_two_db_entries(self, column_name: str = 'state') -> List:
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
            with Database(self.config.db_name, self.config.db_columns) as db:
                records = db.get_last_n_records(2)
                if records:
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
        latest = self.get_latest_db_entry('timestamp')
        if not latest:
            # No recent entry
            return True

        return time() - latest < delta_time

    def check_if_latest_db_state_matches(self, column_name, target_value):
        """
        Check the latest DB entry against a target value
        @param column_name: target column
        @type column_name: str
        @param target_value: target state to match
        @type target_value: str or int
        @return: whether the latest state matches the target
        @rtype: bool
        """
        latest = self.get_latest_db_entry(column_name)
        return latest == target_value
