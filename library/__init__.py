import logging
import os
from typing import TypeVar

HOME_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(HOME_DIR, "config")
TEST_DIR = os.path.join(HOME_DIR, "test")
TEST_CONFIG_DIR = os.path.join(TEST_DIR, "config")
CONFIG_DIRS = [CONFIG_DIR, TEST_CONFIG_DIR]
LOG_DIR = os.path.join(HOME_DIR, "log")


CONFIG_TYPE = TypeVar("CONFIG_TYPE", bound="Base")
CONTROLLER_TYPE = TypeVar("CONTROLLER_TYPE", bound="Base")


class GarageDoorStates:
    OPEN = "Open"
    CLOSED = "Closed"


class GPIODriverCommands:
    TOGGLE = "TOGGLE"
    ON = "ON"
    OFF = "OFF"


class GPIODriverActiveDirection:
    HIGH = "HIGH"
    LOW = "LOW"


def setup_logging(logger, logging_level=False, log_path=None) -> logging.Logger:
    """
    Set up logging stream and file handlers
    @param logger: logger for the module/object we're setting up logging for
    @type logger: logging.Logger
    @param logging_level: logging level as defined by logging package
    @type logging_level: int
    @param log_path: (optional) path for file logging
    @type log_path: str
    @return: logger with handlers setup
    @rtype: logging.Logger
    """
    log_level_str = "DEBUG" if logging_level else "INFO"
    logger.info(f"Logging level: {log_level_str}")

    # stdout stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if logging_level else logging.INFO)

    # stdout logging formatting
    stdout_format = "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
    stdout_formatter = logging.Formatter(stdout_format)
    stream_handler.setFormatter(stdout_formatter)

    # remove existing handlers then add the new one
    logger.handlers = []
    logger.addHandler(stream_handler)

    # set up file handler logger - always debug level
    if not log_path:
        logger.warning("No log file path specified - file logging disabled")
        return logger

    logger.info(f"Logging to file: {log_path}")
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)

    # file logging formatting
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_formatter = logging.Formatter(file_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
