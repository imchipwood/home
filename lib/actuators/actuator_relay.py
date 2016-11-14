from sensor import Sensor, SensorException
import RPi.GPIO as GPIO
import time


class Relay(object):
    """Relay Controller Class

    This class houses all functions required to set up and use
    a relay.
    """

    """Initialize a Garage Door Opener

    Inputs:
        pin number (Integer - GPIO pin)
    Returns:
        Nothing
    """
    def __init__(self, pin):
        super(Relay, self).__init__()
        # set up pins
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    """Clean up GPIO

    Inputs:
        None
    Returns:
        Nothing
    """
    def cleanup(self):
        GPIO.cleanup()

    """'on' relay

    Inputs:
        None
    Returns:
        Nothing
    """
    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)
        self.state = True

    """'off' relay

    Inputs:
        None
    Returns:
        Nothing
    """
    def off(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.state = False

    @property
    def state(self):
        return GPIO.input(self.pin)

    """Toggle the relay

    Inputs:
        None
    Returns:
        None
    """
    def toggle(self):
        if self.state:
            self.off()
            self.on()
        else:
            self.on()
            self.off()
