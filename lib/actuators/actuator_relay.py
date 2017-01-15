import RPi.GPIO as GPIO
from time import sleep

class Relay(object):
    """Relay Controller Class

    This class houses all functions required to set up and use a relay.
    """
    def __init__(self, pin):
        super(Relay, self).__init__()
        GPIO.setmode(GPIO.BCM)
        # set up pin and drive low
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.off()

    def cleanup(self):
        GPIO.cleanup()

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)

    def toggle(self):
        self.on()
        sleep(0.3)
        self.off()

    @property
    def state(self):
        return GPIO.input(self.pin)
