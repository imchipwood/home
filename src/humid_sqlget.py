#!/usr/bin/python
import sys 
import os
import MySQLdb
import argparse
import traceback


sys.path.append('/home/pi/dev/home/lib/db')
from TableAccess import TableAccess

parser = argparse.ArgumentParser()
parser.add_argument('-query', '-q', type=str, default='', help="Type of query - how and what do you want data displayed")
parser.add_argument('-debug', '-d', action="store_true", help="Prevent updates to SQL database, while also printing extra stuff to console. Optional")

args = parser.parse_args()
global sQuery
global bDebug
sQuery = args.query
bDebug = args.debug
if bDebug:
    print "-d- args:"
    print "-d- sQuery: {}".format(sQuery)

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
    sDateCol = sRoomCol = ''
    for col in sqlget['columns']:
        if 'date' in col.lower():
            sDateCol = col
        if 'room' in col.lower():
            sRoomCol = col
    if bDebug:
        print "-d- Columns of interest:\n-d- date: {}\n-d- room: {}".format(sDateCol, sRoomCol)
    
    # do SQL query and format the data
    try:
        # figure out what query to run
        sQueryParsed = queryCheck()
        
        sRoomQuery = 'WHERE '
        if sQueryParsed['room'] != '*':
            sRoomQuery = 'WHERE {}={} AND'.format(sRoomCol, sQueryParsed['room'])
            
        if bDebug:
            print "-d- sQueryParsed = {}".format(sQueryParsed)
            print "-d- sRoomQuery = {}".format(sRoomQuery)
            
        # construct query
        if sQueryParsed['query'] == 'n':
            dbcmd = "SELECT * FROM {0} {1} ORDER BY ID DESC LIMIT {2}".format(sqlget['table'], sRoomQuery.replace(' AND', '') if sQueryParsed['room'] != '*' else '', sQueryParsed['qualifier'])
        elif sQueryParsed['query'] == 'today':
            dbcmd = "SELECT * FROM {0} {1} {2} BETWEEN CURRENT_DATE() AND NOW() ORDER BY ID DESC".format(sqlget['table'], sRoomQuery, sDateCol)
        elif sQueryParsed['query'] == 'date':
            dbcmd = "SELECT * FROM {0} {1} {2} BETWEEN '{3}' AND '{3} 23:59:59' ORDER BY ID DESC".format(sqlget['table'], sRoomQuery, sDateCol, sQueryParsed['qualifier'])
        if bDebug:
            print "-d- MySQL command:\n-d- %s" % (dbcmd)
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

    if bDebug:
        print '-d- Parsing query: "{}"'.format(sQuery)

    # default query if no args are specified (or if empty args specified)
    parsedQuery = {}
    parsedQuery['query'] = 'n'
    parsedQuery['qualifier'] = '5'
    parsedQuery['room'] = '*'
    
    lArgs = sQuery.rstrip().lstrip().split(' ')
    if bDebug:
        print '-d- args split into: "{}"'.format(lArgs)
    # are they any args? If so, parse em. If not, assume default
    if len(lArgs) > 0 and lArgs != ['']:
        # loop thru each arg, populating the parsedQuery dictionary as we go
        for sArg in lArgs:
            # first, deconstruct the arg into a key/value pair
            sKey = value = ''
            sArgSplit = sArg.split('=')
            if len(sArgSplit) == 2:
                sKey = sArgSplit[0].lower()
                value = sArgSplit[1]
            elif len(sArgSplit) == 1:
                if sArgSplit[0].lower() == 'today':
                    sKey = 'today'
                    value = ''
                else:
                    sKey = 'n'
                    value = sArgSplit[0]
            else:
                raise Exception('-E- Something\'s up with your args. Couldn\'t split them into a key/value pair\n\tArgs: {0}\n\tFailed on: {1}'.format(sQuery, sArg))
            if bDebug:
                print "-d- key, value: ({}, {})".format(sKey, value)

            # room
            if sKey == 'room':
                parsedQuery['room'] = '\'{}\''.format(value)
            elif sKey == 'n':
                parsedQuery['query'] = 'n'
                parsedQuery['qualifier'] = int(value)
            elif sKey == 'today':
                parsedQuery['query'] = 'today'
                parsedQuery['qualifier'] = ''
            # date
            elif sKey == 'date':
                # check syntax of date
                sDate = value
                sDateSplit = sDate.split('-')
                dDate = {'year':sDateSplit[0], 'month':sDateSplit[1], 'day':sDateSplit[2]}
                if len(dDate['year']) != 4:
                    raise Exception('-E- Date entered incorrectly - check the year, should be 4 digits.\n\tYear: {}'.format(dDate['year']))
                if len(dDate['month']) != 2:
                    raise Exception('-E- Date entered incorrectly - check the month, should be 2 digits.\n\tMonth: {}'.format(dDate['month']))
                if len(dDate['day']) != 2:
                    raise Exception('-E- Date entered incorrectly - check the day, should be 2 digits.\n\tDay: {}'.format(dDate['day']))
                parsedQuery['query'] = 'date'
                parsedQuery['qualifier'] = sDate

    return parsedQuery


if __name__ == '__main__':
    main()
