#!/usr/bin/python
#from sensor_humidity import Humidity 
import sys 
import os
import MySQLdb
sys.path.append('/home/pi/dev/home/lib/db')
from TableAccess import TableAccess
sys.path.append('/home/pi/dev/home/lib/sensors')
sys.path.append('/home/pi/dev/home/lib/sensors/humidity')
from sensor_humidity import Humidity

def main():
    # set up SQL db
    ta = TableAccess(os.path.dirname(os.path.realpath(__file__))+'/../conf/sql.txt')
    sqlget = ta.getInfo()
    db = MySQLdb.connect('localhost', sqlget['user'], sqlget['pw'], sqlget['table'])
    curs = db.cursor()
    
    # set up the sensor
    h = Humidity(sensor_type='22', pin=4, units='f')
    h.enable()
    try:
        h.read()
        dbcmd =  "INSERT INTO data (tdate, ttime, room, temperature, humidity) values(CURRENT_DATE(), NOW(), 'media', {0:0.1f}, {1:0.1f})".format(h.getTemperature(), h.getHumidity())
        with db:
            curs.execute( dbcmd )
    except KeyboardInterrupt:
        print "\n\tKeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\tSome exception: %s\n" % (e)
        raise e
    return True

if __name__ == '__main__':
    main()
