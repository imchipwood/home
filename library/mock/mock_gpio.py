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

global STATE


def setmode(mode):
    pass


def setup(pin, type, initial=LOW, pull_up_down=PUD_OFF):
    global STATE
    if type == IN:
        if pull_up_down == PUD_OFF:
            STATE = initial
        elif pull_up_down == PUD_UP:
            STATE = HIGH
        else:
            STATE = LOW
    else:
        STATE = initial


def output(pin, direction):
    global STATE
    STATE = direction


def cleanup(pin=None):
    pass


def input(pin):
    return STATE


def add_event_detect(pin, edge, callback=None, bouncetime=200):
    pass


def remove_event_detect(pin):
    pass
