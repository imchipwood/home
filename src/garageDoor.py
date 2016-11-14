#!/usr/bin/python
import sys
import os
import argparse
import traceback
from time import sleep
import timeit
import threading

# sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/db")
# from db_humidity import DBHumidity
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/actuators")
from actuator_relay import Relay
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/sensors")
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
    global bDebug
    global endThreads
    endThreads = False

    # user-defined args
    # sDBAccessFileName = 'sql_humidity_media.txt'

    # set up db
    # sHomeDBPath = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
    # sDBCredentialsFile = sHomeDBPath+'/conf/'+sDBAccessFileName
    # if bDebug:
    #     print "-d- Accessing DB using credentials found here:"
    #     print "-d- {}".format(sDBCredentialsFile)
    # hdb = DBHumidity(sDBCredentialsFile, bDebug=bDebug)

    # set up the sensor
    if bDebug:
        print "-d- Setting up Garage Door Controller"
    gdc = Relay(nPin)
    #gdm = GarageDoorMonitor({'rotary':5, 'limitOpen': 6, 'limitClosed': 7}, bDebug)
    #gdm = GarageDoorMonitor({'rotary':5, 'limitOpen': 6, 'limitClosed': 7}, bDebug)
    gdm = GarageDoorMonitor({'limitOpen': 6, 'limitClosed': 7}, bDebug)

    try:
        # begin monitor thread
        monitorThread = threading.Thread(target=monitor, args=[gdm])
        monitorThread.start()
        #monitorThread.join()
        
        while True:
            sleep(1)

        # insert data into the database
        # hdb.insertData(dData, bDebug)
    except KeyboardInterrupt:
        endThreads = True
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        raise
    except Exception as e:
        endThreads = True
        print "\n\t-E- Some exception: %s\n" % (e)
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
    onehz = 10.0
    #tenhz = 1.0
    lastonehztime = 0
    #lasttenhztime = 0
    while not endThreads:
        now = float(timeit.default_timer())
        print now
        if (now - lastonehztime) > onehz:
            lastonehztime = now
            if bDebug:
                print "-d- gd: monitor thread loop"
            #try:
            m.read()
            print "-d- gd: state: {}".format(m.getDoorState())
            #except:
            #    print "-d- gd: monitor thread exception"
            #    pass
    return
            
            


if __name__ == '__main__':
    main()
