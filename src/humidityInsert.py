#!/usr/bin/python
import sys
import os
import argparse
import traceback

sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/db")
from db_humidity import DBHumidity
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/sensors")
from sensor_humidity import SensorHumidity


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-nAvg",
                        "-n",
                        type=int,
                        default=5,
                        help="# measurements to average. Optional. Default=5")
    parser.add_argument("-insert",
                        "-i",
                        action="store_false",
                        default=True,
                        help="Disable SQL insertion. Defaults to inserting")
    parser.add_argument("-configFile",
                        "-c",
                        type=str,
                        default="sql_humidity_media.txt",
                        help="Config file for SQL database interaction")
    parser.add_argument("-configFileBackup",
                        "-cb",
                        type=str,
                        default=None,
                        help="Config file for backup SQL database interaction")
    parser.add_argument("-debug",
                        "-d",
                        action="store_true",
                        help="Enable debug messages")
    args = parser.parse_args()
    return args


def printData(i, temperature, humidity):
    print ("-d- Temperature[{0}]={1:0.1f}, "
           "Humidity[{0}]={2:0.1f}".format(i,
                                           temperature,
                                           humidity
                                           )
           )
    return

def main():

    parsedArgs = parseArgs()
    iAvg = parsedArgs.nAvg
    sDBAccessFileName = parsedArgs.configFile
    sDBAccessBackupFileName = parsedArgs.configFileBackup
    bInsert = parsedArgs.insert
    bDebug = parsedArgs.debug

    bBackupEnable = True if sDBAccessBackupFileName is not None else False
    # set up db
    sHomeDBPath = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
    sDBCredentialsFile = sHomeDBPath+"/conf/"+sDBAccessFileName
    if bDebug:
        print "-d- Accessing DB using credentials found here:"
        print "-d- {}".format(sDBCredentialsFile)
    hdb = DBHumidity(sDBCredentialsFile, bDebug=bDebug)
    
    if bBackupEnable:
        sDBCredentialsBackupFile = sHomeDBPath+"/conf/"+sDBAccessBackupFileName
        if bDebug:
            print "-d- Accessing backup DB using credentials found here:"
            print "-d- {}".format(sDBCredentialsBackupFile)
        hdbbackup = DBHumidity(sDBCredentialsBackupFile, bDebug=bDebug)

    # set up the sensor
    if bDebug:
        print "-d- Setting up humidity sensor"
    h = SensorHumidity(sensor_type="22", pin=4, units="f")
    try:
        if bDebug:
            print "-d- Beginning 5 warmup readings"
        for i in xrange(0, 5):
            h.read()
            if bDebug:
                printData()

        # take N readings and average them
        if bDebug:
            print "-d- Beginning {} readings for averaging".format(iAvg)
        fTemperature = 0.0
        fHumidity = 0.0
        for i in xrange(0, iAvg):
            h.read()
            if bDebug:
                printData()
            fTemperature += h.getTemperature()
            fHumidity += h.getHumidity()
        fTemperature /= float(iAvg)
        fHumidity /= float(iAvg)
        dData = {"temperature": fTemperature, "humidity": fHumidity}
        if bDebug:
            print "-d- Final data:"
            print "-d- Temperature: {0:0.1f}".format(dData["temperature"])
            print "-d- Humidity:    {0:0.1f}".format(dData["humidity"])

        # insert data into the database
        try:
            hdb.insertData(dData, insert=bInsert, bDebug=bDebug)
        except:
            if bBackupEnable:
                hdbback.insertData(dData, insert=bInsert, bDebug=bDebug)
            else:
                raise
    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e
    return True


if __name__ == "__main__":
    main()
