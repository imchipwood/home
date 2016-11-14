import RPi.GPIO as GPIO


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

    @property
    def state(self):
        return GPIO.input(self.pin)

    def toggle(self):
        if self.state:
            self.off()
            self.on()
        else:
            self.on()
            self.off()
