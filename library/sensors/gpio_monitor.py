"""
Simple GPIO input class
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging

from library.controllers import get_logger

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):  # pragma: no cover
    from . import IS_TEAMCITY

    if IS_TEAMCITY:
        raise
    logging.warning("Failed to import RPi.GPIO - using mock library")
    from library.mock.mock_gpio import GPIO


class GPIOMonitor:
    """
    Simple GPIO monitoring class
    """

    def __init__(self, config, debug=False):
        """
        Constructor for GPIO_Monitor
        @param config: configuration object for GPIO monitoring
        @type config: library.config.gpio_monitor.GPIOMonitorConfig
        @param debug: debug print enable flag
        @type debug: bool
        """
        super()
        self.config = config
        self.logger = get_logger(__name__, debug, config.log)
        GPIO.setmode(GPIO.BCM)
        self.pin = self.config.pin
        self.logger.debug(f"Setting up GPIO on pin {self.pin}")
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=self.pull_up_down)

    @property
    def pull_up_down(self) -> int:
        """
        GPIO Pull direction
        @rtype: int
        """
        if self.config.pull_up_down.lower() == "down":
            return GPIO.PUD_DOWN
        else:
            return GPIO.PUD_UP

    def read(self) -> bool:
        """
        Read the GPIO pin
        @rtype: bool
        """
        return bool(GPIO.input(self.pin))

    def cleanup(self):
        """
        Clean up the GPIO for shutting down the program
        """
        self.logger.debug("GPIO cleanup - removing event detection")
        GPIO.cleanup(self.pin)
