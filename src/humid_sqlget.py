#!/usr/bin/python
import sys 
import os
import MySQLdb
sys.path.append('/home/pi/dev/home/lib/db')
from TableAccess import TableAccess

def main():
    # open SQL db
    ta = TableAccess(os.path.dirname(os.path.realpath(__file__))+'/../conf/sqlget.txt')
    sqlget = ta.getInfo()
    db = MySQLdb.connect('localhost', sqlget['user'], sqlget['pw'], sqlget['table'])
    curs = db.cursor()
    
    # set up the sensor
    try:
        dbcmd =  "SELECT * FROM data ORDER BY ID DESC LIMIT 5"
        with db:
            curs.execute( dbcmd )
        print "\nDate       | Time     | Room     | Temperature | Humidity"
        print "----------------------------------------------------------"
        for reading in curs.fetchall():
            date = "{}".format(reading[0])
            time = "{0:8s}".format(reading[1])
            room = "{0:8s}".format(reading[2])
            temp = "{0:11.1f}".format(reading[3])
            humi = "{0:0.1f}".format(reading[4]) + "%"
            print date + " | " + time + " | " + room + " | " + temp + " | " + humi
    except KeyboardInterrupt:
        print "\n\tKeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\tSome exception: %s\n" % (e)
        raise e
    return True

if __name__ == '__main__':
    main()
