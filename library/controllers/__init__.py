import logging
import os
from abc import ABC, abstractmethod
from multiprocessing import Process
from time import time
from typing import List, Union

from library import setup_logging, CONFIG_TYPE, CONTROLLER_TYPE
from library.communication.mqtt import MQTTClient
from library.config import DatabaseKeys
from library.data import DatabaseEntry, DBType

RUNNING = False


def get_logger(name: str, debug_flag: bool, log_path: str or None) -> logging.Logger:
    """
    Get a logging.Logger
    @param name: name of logger
    @type name: str
    @param debug_flag: debug_flag flag to enable
    @type debug_flag: bool
    @param log_path: optional log file path
    @type log_path: str or None
    @return: Logger with file have
    @rtype: logging.Logger
    """
    # Set up logging
    this_logger = logging.getLogger(name)
    this_logger.setLevel(logging.DEBUG)
    if log_path and not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    logger = setup_logging(
        this_logger,
        logging_level=debug_flag,
        log_path=log_path
    )
    # logger.debug("Logger initialized")
    return logger


class BaseController(ABC):
    """Base class for all controllers to extend"""
    from library.data.central_database import Database, Table
    from library.config import BaseConfiguration

    def __init__(self: CONTROLLER_TYPE, config: CONFIG_TYPE or BaseConfiguration, debug: bool = False):
        super()

        self.debug = debug
        self.config = config  # type: CONFIG_TYPE or BaseConfiguration

        self._mqtt = None
        self.logger = None  # type: logging.Logger or None
        self.thread = None  # type: Process or None

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
        return self.config.db_enabled

    @property
    def db(self) -> Database:
        """
        Get the Database object for this controller
        @rtype: Database
        """
        if self.config.db_type == DBType.CENTRAL:
            from library.data.central_database import Database
            db = Database(
                self.config.db_tables,
                self.config.db_server,
                self.config.db_database_name,
                self.config.db_username,
                self.config.db_password
            )
        else:
            from library.data.local_database import Database
            db = Database(
                self.config.db_tables,
                self.config.db_database_name,
                self.config.db_path
            )
        db.connect()
        return db

    @property
    def db_table(self) -> Table:
        """
        Get the table for writing/reading mqtt data
        @return: Table
        @rtype: Table
        """
        return self.db.get_table(self.db_table_name)

    @property
    def db_table_name(self) -> str:
        """
        Get the table name for writing/reading mqtt data
        @return: name of database table
        @rtype: str
        """
        return self.config.mqtt_config.db_table_name

    def get_entry_for_id(self, convo_id: str) -> Union[DatabaseEntry, None]:
        """
        Get the latest entry for the given ID
        @param convo_id: target conversation ID
        @type convo_id: str
        @return: entry for target convo_id if found, else None
        @rtype: DatabaseEntry or None
        """
        if not self.config.db_enabled or convo_id in ["", None]:
            return None

        self.logger.debug(f"Opening DB {self.config.db_database_name}")
        with self.db as db:
            table = db.get_table(self.db_table_name)
            records = table.get_all_records()
            if not records:
                return None

            matches = [record for record in records if record.get(DatabaseKeys.ID) == convo_id]
            if not matches:
                return None

            if len(matches) > 1:
                self.logger.warning(f"Found multiple records for id {convo_id} - {matches}\nReturning latest")

            return matches[-1]

    def get_latest_db_entry(self, column_name: str or None = None) -> Union[int, float, str, DatabaseEntry, None]:
        """
        Get the latest value from the database
        @param column_name: (Optional) target column name, if None, returns whole row
        @type column_name: str or None
        """
        if not self.config.db_enabled:
            return None

        self.logger.debug(f"Opening DB {self.config.db_enabled}")
        with self.db as db:
            table = db.get_table(self.db_table_name)
            record = table.get_latest_record()
            if not record or all([x is None for x in record.entry]):
                return None

            if column_name:
                latest = record[column_name]
                self.logger.debug(f"Latest db entry at column {column_name}: {latest}")
            else:
                latest = record
                self.logger.debug(f"Latest db entry: {latest}")
        return latest

    def get_last_two_db_entries(self, column_name: str or None = DatabaseKeys.STATE) -> List:
        """
        Get the last two entries from the DB
        @param column_name: (Optional) name of column to get, if None, returns whole rows
        @type column_name: str or None
        @return: list of values from last two entries
        @rtype: list
        """
        if not self.config.db_enabled:
            return []

        self.logger.debug(f"Opening DB {self.config.db_database_name}")
        with self.db as db:
            table = db.get_table(self.db_table_name)
            records = table.get_last_n_records(2)
            if len(records) != 2:
                return []

            if column_name:
                entries = [record[column_name] for record in records]
                self.logger.debug(f"Latest two db entries at column {column_name}: {entries}")
            else:
                entries = records
                self.logger.debug(f"Latest two db entries: {entries}")

            return entries

    def is_entry_recent(self, entry: DatabaseEntry, delta_time: int = 60) -> bool:
        """
        Check if the target entry is 'recent'
        @param entry: entry of interest
        @type entry: DatabaseEntry
        @param delta_time: amount of time to be considered 'recent'
        @type delta_time: int
        @return: whether the entry of interest is 'recent' or not
        @rtype: bool
        """
        return time() - entry[DatabaseKeys.TIMESTAMP] < delta_time if entry else None

    def is_latest_entry_recent(self, delta_time: int = 60) -> bool:
        """
        Check if the latest database entry is 'recent'
        @param delta_time: amount of time to be considered 'recent'
        @type delta_time: int
        @return: whether the latest entry is 'recent' or not
        @rtype: bool
        """
        return self.is_entry_recent(self.get_latest_db_entry(), delta_time)
