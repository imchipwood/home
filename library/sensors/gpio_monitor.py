"""
Simple GPIO input class
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging

from library import setup_logging

try:
    import RPi.GPIO as GPIO
except:
    logging.warning("Failed to import RPi.GPIO - using mock library")
    import library.mock.mock_gpio as GPIO


class GPIO_Monitor(object):
    """
    Simple GPIO monitoring class
    """
    def __init__(self, gpio_pin, debug=False):
        """
        Constructor for GPIO_Monitor
        @param gpio_pin: GPIO pin to read
        @type gpio_pin: int
        @param debug: debug print enable flag
        @type debug: bool
        """
        super(GPIO_Monitor, self).__init__()
        self.logger = setup_logging(
            logging.getLogger(__name__),
            logging_level=debug
        )
        GPIO.setmode(GPIO.BCM)
        self.logger.debug("Setting up GPIO on pin %d", gpio_pin)
        self.pin = gpio_pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        """
        Read the GPIO pin
        @rtype: bool
        """
        return bool(GPIO.input(self.pin))

    def cleanup(self):
        """
        Clean up the GPIO for shutting down the program
        """
        GPIO.cleanup(self.pin)
