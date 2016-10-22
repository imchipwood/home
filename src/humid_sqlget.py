#!/usr/bin/python
import sys 
import os
import MySQLdb
import argparse
import traceback


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

    # user-defined args
    sSQLAccessFileName = 'sql.txt'

    # set up SQL db
    sSQLCredentialsFile = os.path.dirname(os.path.realpath(__file__))+'/../conf/'+sSQLAccessFileName
    if bDebug:
        print "-d- Accessing SQL DB using credentials found here:"
        print "-d- {}".format(sSQLCredentialsFile)
    ta = TableAccess(sSQLCredentialsFile)
    sqlget = ta.getInfo()
    db = MySQLdb.connect('localhost', sqlget['user'], sqlget['pw'], sqlget['db'])
    curs = db.cursor()

    # extract the date column - it's used by most query types
    sDateCol = ''
    for col in sqlget['columns']:
        if 'date' in col.lower():
            sDateCol = col
    
    
    # do SQL query and format the data
    try:
        # figure out what query to run
        sQueryParsed = queryCheck()
        
        # construct query
        if sQueryParsed[0] == 'nEntries':
            dbcmd = "SELECT * FROM {0} ORDER BY ID DESC LIMIT {1}".format(sqlget['table'], sQueryParsed[1])
        elif sQueryParsed[0] == 'today':
            dbcmd = "SELECT * FROM {0} WHERE {1} BETWEEN CURRENT_DATE() AND NOW() ORDER BY ID DESC".format(sqlget['table'], sDateCol)
        elif sQueryParsed[0] == 'date':
            dbcmd = "SELECT * FROM {0} WHERE {1} BETWEEN '{2}' AND '{2} 23:59:59' ORDER BY ID DESC".format(sqlget['table'], sDateCol, sQueryParsed[1])
        # run query
        with db:
            curs.execute( dbcmd )

        # display results
        print "\nDate       | Time     | Room     | Temperature | Humidity"
        print "----------------------------------------------------------"
        lData = curs.fetchall()
        for i in reversed(xrange(len(lData))):
            reading = lData[i]
            date = "{}".format(reading[0])
            time = "{0:8s}".format(reading[1])
            room = "{0:8s}".format(reading[2])
            temp = "{0:11.1f}".format(reading[3])
            humi = "{0:0.1f}".format(reading[4]) + "%"
            print date + " | " + time + " | " + room + " | " + temp + " | " + humi

    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e
    return True

def queryCheck():
    global sQuery
    global bDebug

    lValidQueryTypes = ['days', 'date']

    # first, split by spaces - how many args are there?
    # behave differently for 1 or 2 args
    parsedQuery = []
    lArgs = sQuery.lower().rstrip().lstrip().split(' ')
    nArgs = len(lArgs)
    if nArgs < 1 or nArgs > 2:
        raise Exception('-E- Too many or too few args, bruh, not sure what to do.\n\tArgs: {}'.format(sQuery))
    elif nArgs == 1:
        if bDebug:
            print "-d- 1 arg"
        # check if user wants today or nEntries
        if 'today' in lArgs[0]:
            parsedQuery = ['today', '']
        else:
            parsedQuery = ['nEntries', int(lArgs[0])]
    elif nArgs == 2:
        if bDebug:
            print "-d- 2 args"
        # date
        if lArgs[0] == 'date':
            # check syntax of date
            sDate = lArgs[1]
            sDateSplit = sDate.split('-')
            dDate = {'year':sDateSplit[0], 'month':sDateSplit[1], 'day':sDateSplit[2]}
            if len(dDate['year']) != 4:
                raise Exception('-E- Date entered incorrectly - check the year, should be 4 digits.\n\tYear: {}'.format(dDate['year']))
            if len(dDate['month']) != 2:
                raise Exception('-E- Date entered incorrectly - check the month, should be 2 digits.\n\tMonth: {}'.format(dDate['month']))
            if len(dDate['day']) != 2:
                raise Exception('-E- Date entered incorrectly - check the day, should be 2 digits.\n\tDay: {}'.format(dDate['day']))
            parsedQuery = ['date', sDate]
    return parsedQuery


if __name__ == '__main__':
    main()
