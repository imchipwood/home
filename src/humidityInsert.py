#!/usr/bin/python
import sys
import os
import argparse
import traceback

sys.path.append('/home/pi/dev/home/lib/db')
from db_humidity import DBHumidity
sys.path.append('/home/pi/dev/home/lib/sensors')
from sensor_humidity import SensorHumidity

parser = argparse.ArgumentParser()
parser.add_argument('-nAvg', '-n', type=int, default=5, help="Number of measurements to average before logging. Optional. Defaults to 5")
parser.add_argument('-debug', '-d', action="store_true", help="Prevent updates to database, while also printing extra stuff to console. Optional")

args = parser.parse_args()
global iAvg
global bDebug
iAvg = args.nAvg
bDebug = args.debug


def main():
    global iAvg
    global bDebug

    # user-defined args
    sDBAccessFileName = 'sql.txt'

    # set up db
    sDBCredentialsFile = os.path.dirname(os.path.realpath(__file__))+'/../conf/'+sDBAccessFileName
    if bDebug:
        print "-d- Accessing DB using credentials found here:"
        print "-d- {}".format(sDBCredentialsFile)
    hdb = DBHumidity(sDBCredentialsFile, bDebug=bDebug)

    # set up the sensor
    if bDebug:
        print "-d- Setting up humidity sensor"
    h = SensorHumidity(sensor_type='22', pin=4, units='f')
    try:
        if bDebug:
            print "-d- Beginning 5 warmup readings"
        for i in xrange(0, 5):
            h.read()
            if bDebug:
                print "-d- Temperature[{0}]={1:0.1f}, Humidity[{0}]={2:0.1f}".format(i, h.getTemperature(), h.getHumidity())

        # take N readings and average them
        if bDebug:
            print "-d- Beginning {} readings for averaging".format(iAvg)
        fTemperature = 0.0
        fHumidity = 0.0
        for i in xrange(0, iAvg):
            h.read()
            if bDebug:
                print "-d- Temperature[{0}]={1:0.1f}, Humidity[{0}]={2:0.1f}".format(i, h.getTemperature(), h.getHumidity())
            fTemperature += h.getTemperature()
            fHumidity += h.getHumidity()
        fTemperature /= float(iAvg)
        fHumidity /= float(iAvg)
        dData = {'temperature':fTemperature, 'humidity':fHumidity}
        if bDebug:
            print '-d- Final Temperature: {0:0.1f}'.format(dData['temperature'])
            print '-d- Final Humidity:    {0:0.1f}'.format(dData['humidity'])

        # insert data into the database
        hdb.insertData(dData, bDebug)
    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e
    return True

if __name__ == '__main__':
    main()
