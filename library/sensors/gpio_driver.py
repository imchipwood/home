"""
Simple GPIO output class
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging
import time

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

        self.pin = self.config.pin
        self.logger.debug(f"Setting up GPIO on pin {self.pin}")

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.write_off()

    @property
    def is_active_high(self) -> bool:
        """
        Check if GPIO is defined as active high
        @rtype: bool
        """
        return self.config.active_direction == GPIO.HIGH

    @property
    def off_state(self) -> int:
        """
        Get state for GPIO OFF based on active low/high
        @rtype: int
        """
        return GPIO.LOW if self.is_active_high else GPIO.HIGH

    @property
    def on_state(self) -> int:
        """
        Get state for GPIO ON based on active low/high
        @rtype: int
        """
        return GPIO.HIGH if self.is_active_high else GPIO.LOW

    def write(self, direction: int):
        """
        Write to the GPIO pin
        @param direction: GPIO.HIGH or GPIO.LOW
        @type direction: int
        """
        GPIO.output(self.pin, direction)

    def write_off(self):
        """
        Set GPIO to OFF state
        """
        self.write(self.off_state)

    def write_on(self):
        """
        Set GPIO to ON state
        """
        self.write(self.on_state)

    def toggle(self):
        """
        Toggle based on config settings
        """
        self.write_off()
        time.sleep(self.config.toggle_delay)
        self.write_on()
        time.sleep(self.config.toggle_delay)
        self.write_off()

    def cleanup(self):
        """
        Clean up the GPIO for shutting down the program
        """
        self.logger.debug("GPIO cleanup - removing event detection")
        GPIO.cleanup(self.pin)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
