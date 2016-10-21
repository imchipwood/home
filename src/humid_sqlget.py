#!/usr/bin/python
import sys 
import os
import MySQLdb
import argparse

sys.path.append('/home/pi/dev/home/lib/db')
from TableAccess import TableAccess

parser = argparse.ArgumentParser()
parser.add_argument('-query', '-q', type=str, default='recent', help="Type of query - how and what do you want data displayed")
parser.add_argument('-debug', '-d', action="store_true", help="Prevent updates to SQL database, while also printing extra stuff to console. Optional")

args = parser.parse_args()
global sQuery
global bDebug
sQuery = args.query
bDebug = args.debug
if bDebug:
    print "args:"
    print "sQuery: {}".format(sQuery)

def main():
    global sQuery
    global bDebug
    
    # open SQL db
    ta = TableAccess(os.path.dirname(os.path.realpath(__file__))+'/../conf/sqlget.txt')
    sqlget = ta.getInfo()
    db = MySQLdb.connect('localhost', sqlget['user'], sqlget['pw'], sqlget['db'])
    curs = db.cursor()
    
    # do SQL query and format the data
    try:
        dbcmd = "SELECT * FROM data ORDER BY ID DESC LIMIT 5"
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
