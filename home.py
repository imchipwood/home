"""
Entry point for all Raspberry Pi-based home automation sensors
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""

import argparse
import logging

from library.config import ConfigurationHandler


def parse_args():
    """
    Set up an argument parser and return the parsed arguments
    @return: Parsed commandline args
    @rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Python 3.x RPi Home Automation Entry Point"
    )
    parser.add_argument(
        "configpath",
        type=str,
        help="Configuration file path for sensor setup. Supported types: JSON"
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


def execute():
    """
    Full flow - get arguments, parse configuration files, launch threads
    """
    args = parse_args()
    handler = ConfigurationHandler(config_path=args.configpath)

    try:
        logging.info("Launching sensor threads")
        for sensor in handler:
            sensor.start()

        # Infinite loop while threads run
        logging.info("Sensor threads launched - looping forever")
        while True:
            pass

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - exiting gracefully")

    finally:
        logging.info("Cleaning up sensor threads")
        for sensor in handler:
            try:
                sensor.cleanup()
            except:
                logging.exception("Exception cleaning up sensor %s", sensor)


if __name__ == "__main__":
    execute()
