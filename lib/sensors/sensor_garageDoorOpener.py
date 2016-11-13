import Adafruit_DHT
from sensor import Sensor, SensorException
import RPi.GPIO as GPIO


class GarageDoorOpener(Sensor):
    """Garage Door Opener Class

    This class houses all functions required to set up and use
    a relay to control a garage door motor.
    """
    bDebug = False

    """Initialize a Garage Door Opener

    Inputs:
        pin number (Integer - GPIO pin)
        debug (Boolean)
    Returns:
        Nothing
    """
    def __init__(self, pin, debug=False):
        super(GarageDoorOpener, self).__init__()
        self.bDebug = debug
        # set up pins
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    """Take readings

    Inputs:
        None
    Returns:
        Nothing
    """
    def read(self):
        return

    """Get current units - not relevant for garage door detector

    Inputs:
        None
    Returns:
        None
    """
    def getUnits(self):
        return

    """Update temperature units

    Inputs:
        units - whatever you want, it's unused
    Returns:
        None
    """
    def setUnits(self, units):
        return

    """'on' relay

    Inputs:
        None
    Returns:
        Nothing
    """
    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    """'off' relay

    Inputs:
        None
    Returns:
        Nothing
    """
    def off(self):
        GPIO.output(self.pin, GPIO.LOW)

    """Check the state of the relay

    Inputs:
        None
    Returns:
        True if GPIO pin state matches internal state boolean, false otherwise
    """
    def checkState(self):
        return GPIO.input(self.pin) != self.state

    """Toggle the relay

    Inputs:
        None
    Returns:
        None
    """
    def toggle(self):
        self.on()
        self.off()
