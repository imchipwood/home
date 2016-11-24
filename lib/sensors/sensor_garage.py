
import os
import sys
from sensor_gdMonitor import GarageDoorMonitor

sHomePath = os.path.dirname(os.path.realpath(__file__))
sHomePath = "/".join(sHomePath.split("/")[:-1])
print sHomePath
sys.path.append(sHomePath+"/db")
from db_home import DBHome


class Garage(DBHome, GarageDoorMonitor):
    def __init__(self, f, debug=False):
        super(DBHome, self).__init__()
        super(GarageDoorMonitor, self).__init__()
