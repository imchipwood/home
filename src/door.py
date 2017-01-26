#!/usr/bin/python
import sys
import os
import argparse
import traceback

# globals
global sHomePath

# stupidity until I figure out how to package my libs properly
sHomePath = os.path.dirname(os.path.realpath(__file__))
sHomePath = "/".join(sHomePath.split("/")[:-1])
while "home" not in sHomePath.split("/")[-1]:
    sHomePath = "/".join(sHomePath.split("/")[:-1])

sys.path.append(sHomePath+"/lib/sensors")
from doorController import DoorController


def parseArgs():
    # argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-configFile",
                        "-c",
                        type=str,
                        default="garageDoor.txt",
                        help="Config file for DoorController")
    parser.add_argument('-debug',
                        '-d',
                        action="store_true",
                        help="Enable debug messages")

    args = parser.parse_args()
    return args


def main():
    global sHomePath
    global endThreads
    endThreads = False

    parsedArgs = parseArgs()
    sGarageDoorFileName = parsedArgs.configFile
    bDebug = parsedArgs.debug

    sGarageDoorFile = sHomePath+"/conf/"+sGarageDoorFileName
    try:
        door = DoorController(sGarageDoorFile, bDebug)
    except:
        raise

    try:
        door.start()
        while True:
            sleep(10)
    except KeyboardInterrupt:
        print("\n\t-e- gd: KeyboardInterrupt, exiting gracefully\n")
        raise
    except Exception as e:
        print("\n\t-E- gd: Some exception: %s\n" % (e))
        traceback.print_exc()
        raise e
    finally:
        door.cleanup()
    return


if __name__ == '__main__':
    main()
