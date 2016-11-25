#!/usr/bin/python
import sys
import os
import argparse
import traceback
from time import sleep
import timeit
import threading

# globals
global sHomePath
global endThreads

# stupidity until I figure out how to package my libs properly
sHomePath = os.path.dirname(os.path.realpath(__file__))
sHomePath = "/".join(sHomePath.split("/")[:-1])
while "home" not in sHomePath.split("/")[-1]:
    sHomePath = "/".join(sHomePath.split("/")[:-1])

sys.path.append(sHomePath+"/lib/actuators")
from actuator_relay import Relay
sys.path.append(sHomePath+"/lib/sensors")
from sensor_gdMonitor import GarageDoorMonitor
sys.path.append(sHomePath+"/lib/db")
from db_home import DBHome


def parseArgs():
    # argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-insert",
                        "-i",
                        action="store_false",
                        default=True,
                        help="Disable SQL insertion. Defaults to inserting")
    parser.add_argument("-configFile",
                        "-c",
                        type=str,
                        default="garageMonitor.txt",
                        help="Config file for SQL database interaction")
    parser.add_argument("-configFileBackup",
                        "-cb",
                        type=str,
                        default=None,
                        help="Config file for backup SQL database interaction")
    parser.add_argument('-debug',
                        '-d',
                        action="store_true",
                        help="Enable debug messages, also disable SQL injection")

    args = parser.parse_args()
    return args


def main():
    global sHomePath
    global endThreads
    endThreads = False

    parsedArgs = parseArgs()
    sGarageDoorFileName = parsedArgs.configFile
    sGarageDoorBackupFileName = parsedArgs.configFileBackup
    bInsert = parsedArgs.insert
    bDebug = parsedArgs.debug

    bBackupEnable = True if sGarageDoorBackupFileName is not None else False

    sGarageDoorFile = sHomePath+"/conf/"+sGarageDoorFileName

    # set up DBs
    # if bDebug:
    #     print "-d- Accessing DB using credentials found here:"
    #     print "-d- {}".format(sGarageDoorFile)
    # hdb = DBHome(sGarageDoorFile, bDebug=bDebug)

    # hdbackup = None
    # if bBackupEnable:
    #     sGarageDoorBackupFile = sHomeDBPath+"/conf/"+sGarageDoorBackupFileName
    #     if bDebug:
    #         print "-d- Accessing backup DB using credentials found here:"
    #         print "-d- {}".format(sGarageDoorBackupFile)
    #     hdbackup = DBHumidity(sGarageDoorBackupFile, bDebug=bDebug)
    try:
        gdm = GarageDoorMonitor(sGarageDoorFile, bDebug)
    except:
        raise
    try:
        # if nPinRelay is not None:
        #     controlThread = threading.Thread(target=control, args=[gdc, bDebug])
        #     controlThread.start()

        while not endThreads:
            1
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
        # if nPinRelay is not None:
        #     gdc.cleanup()
        gdm.cleanup()
    return


def control(c, bDebug):
    global endThreads
    onehz = 1.0
    lastonehztime = 0
    while not endThreads:
        now = float(timeit.default_timer())
        if (now - lastonehztime) > onehz:
            lastonehztime = now
            if bDebug:
                print "-d- gd: control thread"
            # Uh, to be honest, I hadn't thought about how to control it yet.
            # Brilliant, I know
            # TODO: control thread - where to get relay toggle signal?
    return


if __name__ == '__main__':
    main()
