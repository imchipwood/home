class GPIO:
    HIGH = 1
    LOW = 0
    OUT = 0
    IN = 1
    RISING = 31
    FALLING = 32
    BOTH = 33
    BCM = 11
    PUD_UP = 22
    PUD_DOWN = 21
    PUD_OFF = 20

    STATE = {}

    @classmethod
    def setmode(cls, mode):
        pass

    @classmethod
    def setup(cls, pin, direction, initial=LOW, pull_up_down=PUD_OFF):
        if pin not in cls.STATE:
            cls.STATE[pin] = cls.LOW
        if direction == cls.IN:
            if pull_up_down == cls.PUD_OFF:
                cls.STATE[pin] = initial
            elif pull_up_down == cls.PUD_UP:
                cls.STATE[pin] = cls.HIGH
            else:
                cls.STATE[pin] = cls.LOW
        else:
            cls.STATE[pin] = initial

    @classmethod
    def output(cls, pin, direction):
        cls.STATE[pin] = direction

    @classmethod
    def cleanup(cls, pin=None):
        if pin:
            if pin in cls.STATE:
                del cls.STATE[pin]
        else:
            pins = cls.STATE.keys()
            for pin in pins:
                del cls.STATE[pin]

    @classmethod
    def input(cls, pin):
        return cls.STATE.get(pin)

    @classmethod
    def add_event_detect(cls, pin, edge, callback=None, bouncetime=200):
        pass

    @classmethod
    def remove_event_detect(cls, pin):
        pass
