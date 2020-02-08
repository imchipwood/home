"""
Entry point for all Raspberry Pi-based home automation sensors
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""

import argparse
from library.home import execute


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


if __name__ == "__main__":
    args = parse_args()
    execute(args.configpath, debug=args.debug)
