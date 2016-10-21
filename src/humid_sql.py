#!/usr/bin/python
#from sensor_humidity import Humidity 
import sys 
import os
import MySQLdb
import argparse

sys.path.append('/home/pi/dev/home/lib/db')
from TableAccess import TableAccess
sys.path.append('/home/pi/dev/home/lib/sensors')
sys.path.append('/home/pi/dev/home/lib/sensors/humidity')
from sensor_humidity import Humidity

parser = argparse.ArgumentParser()
parser.add_argument('-nAvg', '-n', type=int, default=5, help="Number of measurements to average before logging. Optional. Defaults to 5")
parser.add_argument('-debug', '-d', action="store_true", help="Prevent updates to SQL database, while also printing extra stuff to console. Optional")

args = parser.parse_args()
global iAvg
global bDebug
iAvg = args.nAvg
bDebug = args.debug


def main():
    global iAvg
    global bDebug
    
    # user-defined args
    sSQLAccessFileName = 'sql.txt'
    
    # set up SQL db
    sSQLCredentialsFile = os.path.dirname(os.path.realpath(__file__))+'/../conf/'+sSQLAccessFileName
    if bDebug:
        print "-d- Accessing SQL DB using credentials found here:"
        print "-d- {}".format(sSQLCredentialsFile)
    ta = TableAccess(sSQLCredentialsFile)
    sqlget = ta.getInfo()
    if bDebug:
        print "-d- SQL Database info:"
        print "-d- Database: {}".format(sqlget['db'])
        print "-d- Table:    {}".format(sqlget['table'])
        print "-d- User:     {}".format(sqlget['user'])
        print "-d- Columns:  {}".format(sqlget['columns'])
        print "-d- Room:     {}".format(sqlget['room'])
    db = MySQLdb.connect('localhost', sqlget['user'], sqlget['pw'], sqlget['db'])
    curs = db.cursor()
    
    # set up the sensor
    if bDebug:
        print "-d- Setting up humidity sensor"
    h = Humidity(sensor_type='22', pin=4, units='f')
    h.enable()
    try:
        if bDebug:
            print "-d- Beginning readings"
        # take N readings and average them
        fTemperature = 0.0
        fHumidity = 0.0
        for i in xrange(0,iAvg):
            h.read()
            if bDebug:
                print "-d- Temperature[{0}]={1:0.1f}, Humidity[{0}]={2:0.1f}".format(i, h.getTemperature(), h.getHumidity())
            fTemperature += h.getTemperature()
            fHumidity += h.getHumidity()
        fTemperature /= float(iAvg)
        fHumidity /= float(iAvg)
        if bDebug:
            print '-d- Final Temperature: {0:0.1f}'.format(fTemperature)
            print '-d- Final Humidity:    {0:0.1f}'.format(fHumidity)
        # Generate SQL command and execute
        sColumns = ', '.join(sqlget['columns'])
        dbcmd =  "INSERT INTO {0} ({1}) values(CURRENT_DATE(), NOW(), '{2}', {3:0.1f}, {4:0.1f})".format(sqlget['table'], sColumns, sqlget['room'], fTemperature, fHumidity)
        if bDebug:
            print "-d- MySQL command (will not be run):\n-d- %s" % (dbcmd)
        else:
            with db:
                curs.execute( dbcmd )
    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        raise e
    return True

if __name__ == '__main__':
    main()
