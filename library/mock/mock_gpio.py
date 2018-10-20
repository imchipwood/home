HIGH = 1
LOW = 0
OUT = 1
IN = 0
BCM = 'bcm'
PUD_UP = True
PUD_DOWN = False
PUD_OFF = None

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
