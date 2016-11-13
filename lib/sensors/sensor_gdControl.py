from sensor import Sensor, SensorException
import RPi.GPIO as GPIO


class GarageDoorController(Sensor):
    """Garage Door Controller Class

    This class houses all functions required to set up and use
    a relay to control a garage door motor.
    """
    bDebug = False
    bRelay = False

    """Initialize a Garage Door Opener

    Inputs:
        pin number (Integer - GPIO pin)
        debug (Boolean)
    Returns:
        Nothing
    """
    def __init__(self, pin, debug=False):
        super(GarageDoorController, self).__init__()
        self.bDebug = debug
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
        self.bRelay = False

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
        self.bRelay = True

    """'off' relay

    Inputs:
        None
    Returns:
        Nothing
    """
    def off(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.bRelay = False

    """Check the state of the relay

    Inputs:
        None
    Returns:
        True if GPIO pin state matches internal state boolean, false otherwise
    """
    def checkRelay(self):
        GPIO.setup(self.pin, GPIO.IN)
        bState = GPIO.input(self.pin) != self.bRelay
        GPIO.setup(self.pin, GPIO.OUT)
        return bState

    """Toggle the relay

    Inputs:
        None
    Returns:
        None
    """
    def toggle(self):
        self.on()
        self.off()
