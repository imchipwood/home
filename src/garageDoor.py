#!/usr/bin/python
import sys
import os
import argparse
import traceback
from time import sleep
import timeit
import threading

global sHomePath
sHomePath = os.path.dirname(os.path.realpath(__file__))
sHomePath = "/".join(sHomePath.split("/")[:-1])
# sys.path.append(sHomePath+"/lib/db")
# from db_humidity import DBHumidity
sys.path.append(sHomePath+"/lib/actuators")
from actuator_relay import Relay
sys.path.append(sHomePath+"/lib/sensors")
from sensor_gdMonitor import GarageDoorMonitor

parser = argparse.ArgumentParser()
parser.add_argument('-pin',
                    '-p',
                    type=int,
                    default=5,
                    help="Pin # for relay")
parser.add_argument('-debug',
                    '-d',
                    action="store_true",
                    help="Enable debug messages, also disable SQL injection")

args = parser.parse_args()
global nPin
global bDebug
nPin = args.pin
bDebug = args.debug

global endThreads


def main():
    global nPin
    global sHomePath
    global bDebug
    global endThreads
    endThreads = False

    # user-defined args
    # sDBAccessFileName = 'sql_humidity_media.txt'

    # set up db
    # sDBCredentialsFile = sHomePath+'/conf/'+sDBAccessFileName
    # if bDebug:
    #     print "-d- Accessing DB using credentials found here:"
    #     print "-d- {}".format(sDBCredentialsFile)
    # hdb = DBHumidity(sDBCredentialsFile, bDebug=bDebug)

    # set up the sensor
    if bDebug:
        print "-d- gd: Setting up Garage Door Controller"
    gdc = Relay(nPin)
    gdm = GarageDoorMonitor(
        {'rotary': 5,
         'limitOpen': 6,
         'limitClosed': 7},
        bDebug)

    try:
        # begin monitor thread
        monitorThread = threading.Thread(target=monitor, args=[gdm])
        monitorThread.start()
        controlThread = threading.Thread(target=control, args=[gdc])
        controlThread.start()

        while True:
            sleep(1)

        # insert data into the database
        # hdb.insertData(dData, bDebug)
    except KeyboardInterrupt:
        endThreads = True
        print "\n\t-e- gd: KeyboardInterrupt, exiting gracefully\n"
        raise
    except Exception as e:
        endThreads = True
        print "\n\t-E- gd: Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e
    finally:
        endThreads = True
        gdc.cleanup()
        gdm.cleanup()
    return


def monitor(m):
    global endThreads
    global bDebug
    onehz = 1.0
    lastonehztime = 0
    while not endThreads:
        now = float(timeit.default_timer())
        if (now - lastonehztime) > onehz:
            lastonehztime = now
            if bDebug:
                print "-d- gd: monitor thread"
            try:
                m.read()
                if bDebug:
                    print "-d- gd: monitor thread state: %s" % m.getDoorState()
            except Exception as e:
                if bDebug:
                    print "-d- gd: monitor exception"
                traceback.print_exc()
                endThread = True
                raise
    return


def control(c):
    global endThreads
    global bDebug
    onehz = 1.0
    lastonehztime = 0
    while not endThreads:
        now = float(timeit.default_timer())
        if (now - lastonehztime) > onehz:
            lastonehztime = now
            if bDebug:
                print "-d- gd: control thread"


if __name__ == '__main__':
    main()
