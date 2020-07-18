import logging

from library.config import ConfigurationHandler


def execute(config_path, stop=lambda: False, debug=False):
    """
    Full flow - get arguments, parse configuration files, launch threads
    @param config_path: path to config file
    @type config_path: str
    @param stop: method to stop the process
    @type stop: method
    @param debug: debug flag
    @type debug: bool
    """
    handler = ConfigurationHandler(config_path=config_path, debug=debug)

    try:
        logging.info("Launching sensor threads")
        for sensor in handler:
            sensor.start()

        # Infinite loop while threads run
        logging.info("Sensor threads launched - looping forever")
        while not stop():
            pass

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - exiting gracefully")

    finally:
        logging.info("Cleaning up sensor threads")
        for sensor in handler:
            try:
                sensor.cleanup()
            except:
                logging.exception(f"Exception cleaning up sensor {sensor}")
