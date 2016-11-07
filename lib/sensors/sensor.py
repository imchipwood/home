"""Sensor class

Base class for all sensors of home network.
"""

from abc import abstractmethod


class Sensor(object):
    state = False

    def __init__(self):
        super(Sensor, self).__init__()

    """Enable the sensor
    Inputs:
        None
    Returns:
        Nothing
    """
    def enable(self):
        self.state = True

    """Disable the sensor
    Inputs:
        None
    Returns:
        Nothing
    """
    def disable(self):
        self.state = False

    """Return state of sensor
    Inputs:
        None
    Returns:
        self.state - Boolean reflecting sensor status
    """
    def getState(self):
        return self.state

    @abstractmethod
    def read(self):
        """Trigger a sensor reading. Function should not return anything."""

    @abstractmethod
    def setUnits(self, units):
        """Update the units this sensor is storing data in"""

    @abstractmethod
    def getUnits(self):
        """Return the units this sensor is storing data in"""


class SensorException(Exception):
    def __init__(self, message):
        super(SensorException, self).__init__(message)
