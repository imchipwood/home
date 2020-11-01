import os
import random

IS_TEAMCITY = os.environ.get("IS_TEAMCITY", "FALSE") == "TRUE"


def avg(l):
    """
    Average the values in a list
    @param l: list of floats or ints
    @type l: list[float]
    @return: average of values in list
    @rtype: float
    """
    return sum(l) / len(l)


class SensorError(Exception):
    pass


class SensorBase:
    """
    Base sensor class
    """
    random = random.Random()

    def __init__(self):
        """
        Constructor for base sensor class
        """
        super()
        self.random.seed()

    @classmethod
    def get_id(cls) -> str:
        """
        Get a new random ID
        @return: new random ID as a string
        @rtype: str
        """
        return str(int(cls.random.random() * 2 ** 32))
