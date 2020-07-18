"""
Simple GPIO output class
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging

from library.controllers import get_logger

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError, ModuleNotFoundError):  # pragma: no cover
    from . import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Failed to import RPi.GPIO - using mock library")
    from library.mock.mock_gpio import GPIO


class GPIODriver:
    """
    Simple GPIO output class
    """

    def __init__(self, config, debug=False):
        """
        Constructor for GPIODriver
        @param config: configuration object for GPIO driving
        @type config: library.config.gpio_driver.GPIODriverConfig
        @param debug: debug print enable flag
        @type debug: bool
        """
        super()
        self.config = config
        self.logger = get_logger(__name__, debug, config.log)
        GPIO.setmode(GPIO.BCM)
        self.pin = self.config.pin
        self.logger.debug(f"Setting up GPIO on pin {self.pin}")
        GPIO.setup(self.pin, GPIO.OUT)
        self.write(GPIO.LOW if self.config.toggle_direction == GPIO.HIGH else GPIO.HIGH)

    def write(self, direction: int):
        """
        Write to the GPIO pin
        @param direction: GPIO.HIGH or GPIO.LOW
        @type direction: int
        """
        GPIO.output(self.pin, direction)

    def cleanup(self):
        """
        Clean up the GPIO for shutting down the program
        """
        self.logger.debug("GPIO cleanup - removing event detection")
        GPIO.cleanup(self.pin)