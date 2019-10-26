"""
Simple GPIO input class
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""
import logging

from library.controllers import Get_Logger

try:
    import RPi.GPIO as GPIO
except:
    logging.warning("Failed to import RPi.GPIO - using mock library")
    import library.mock.mock_gpio as GPIO


class GPIO_Monitor(object):
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
        super().__init__()
        self.config = config
        self.logger = Get_Logger(__name__, debug, config.log)
        GPIO.setmode(GPIO.BCM)
        self.pin = self.config.pin
        self.logger.debug(f"Setting up GPIO on pin {self.pin}")
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=self.pull_up_down)

    @property
    def pull_up_down(self):
        """
        GPIO Pull direction
        @rtype: bool
        """
        if self.config.pull_up_down.lower() == "down":
            return GPIO.PUD_DOWN
        else:
            return GPIO.PUD_UP

    def add_both_event_detection(self, callback=None, bouncetime=200):
        """
        Add rising and falling event detection
        @param callback: callback to use on event fired
        @type callback: method
        @param bouncetime: software debounce time in ms
        @type bouncetime: int
        """
        GPIO.add_event_detect(self.pin, rising_or_falling=GPIO.BOTH, callback=callback, bouncetime=bouncetime)

    def add_rising_event_detection(self, callback=None, bouncetime=200):
        """
        Add rising event detection
        @param callback: callback to use on event fired
        @type callback: method
        @param bouncetime: software debounce time in ms
        @type bouncetime: int
        """
        GPIO.add_event_detect(self.pin, rising_or_falling=GPIO.RISING, callback=callback, bouncetime=bouncetime)

    def add_falling_event_detection(self, callback=None, bouncetime=200):
        """
        Add falling event detection
        @param callback: callback to use on event fired
        @type callback: method
        @param bouncetime: software debounce time in ms
        @type bouncetime: int
        """
        GPIO.add_event_detect(self.pin, rising_or_falling=GPIO.FALLING, callback=callback, bouncetime=bouncetime)

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
