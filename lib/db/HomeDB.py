# SQL Library
#
# The intention of this file is to consolidate all 
# SQL interactions into a single library,
# thereby de-cluttering the scripts coordinating
# sensor reading, data logging, etc.

import os
import MySQLdb
import traceback

class HomeDB(object):
    db = ''
    curs = ''
    dbcmd = ''
    dataRaw = []
    dataFormatted = []
    
    __conf = {'db':'', 'table':'', 'user':'', 'pw':'', 'room':'', 'columns':[]}
    sConfFile = ''
    
    def __init__(self, f):
        super(HomeDB, self).__init__()
        
        # read config file
        if os.path.exists(f):
            self.sConfFile = f
        else:
            raise IOError('-E- HomeDB Error: Please check if the specified DB config file exists: {}'.format(f))
        
        if self.readConfig():
            # open up database
            try:
                self.db = MySQLdb.connect('localhost', self.__conf['user'], self.__conf['pw'], self.__conf['db'])
                self.curs = self.db.cursor()
            except:
                raise IOError('-E- HomeDB Error: Failed to open database. Please check config')
        else:
            raise IOError('-E- HomeDB Error: Failed to properly parse DB config file: {}'.format(self.sConfFile))

    """ Read config file and get MySQL database info out of it
        Inputs:
            None
        Returns:
            True if config was parsed properly, false otherwise
        
    """
    def readConfig(self):
        confTemp = {}
        with open(self.sConfFile, 'r') as inf:
            for line in inf:
                line = line.rstrip().split('=')
                # database
                if line[0] == 'db':
                    confTemp['db'] = line[-1]
                # table
                if line[0] == 't':
                    confTemp['table'] = line[-1]
                # username
                if line[0] == 'u':
                    confTemp['user'] = line[-1]
                # password
                if line[0] == 'p':
                    confTemp['pw'] = line[-1]
                # room
                if line[0] == 'r':
                    confTemp['room'] = line[-1]
                # columns to populate
                if line[0] == 'c':
                    confTemp['columns'] = line[-1].split(',')
        # check for blanks
        validConf = not '' in [confTemp['db'], confTemp['table'], confTemp['user'], confTemp['pw']]
        if not validConf:
            print "-E- HomeDB Error: something's up with the db, table, user, or pw fields in your config file"
        validConf = not '' in confTemp['columns']
        if not validConf:
            print "-E- HomeDB Error: something's up with the columns field in your config file"
        if not 'get' in self.sConfFile.lower():
            validConf = not '' in [confTemp['room']]
            if not validConf:
                print "-E- HomeDB Error: something's up with the room field in your config file"
        if validConf:
            self.__conf = confTemp
        return validConf
        
    """ Construct a query based on string input
        Inputs:
            sQuery - the query as a string. 
                Valid query options:
                    n=<number> - get the last <number> entries
                    today - get all entries from today
                    room=<room> - pull data only from <room>
                    date=<year>-<month>-<day> - get all entries for a particular date where year is a 4 digit # and month/day are 2 digits
                Default query if no options are specified - 'n=5 room=*'
            bDebug - (optional) flag to print more info to console
        Returns:
            SQL command as a string
                    
    """
    def constructQuery(self, sQuery, bDebug=False):
        
        if bDebug:
            print '-d- Parsing query: "{}"'.format(sQuery)
    
        # default query if no args are specified (or if empty args specified)
        dQuery = {}
        dQuery['query'] = 'n'
        dQuery['qualifier'] = '5'
        dQuery['room'] = '*'
        
        lArgs = sQuery.rstrip().lstrip().split(' ')
        if bDebug:
            print '-d- args split into: "{}"'.format(lArgs)
        # are they any args? If so, parse em. If not, assume default
        if len(lArgs) > 0 and lArgs != ['']:
            # loop thru each arg, populating the dQuery dictionary as we go
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
    
                # room specification
                if sKey == 'room':
                    dQuery['room'] = '\'{}\''.format(value)
                # nEntries
                elif sKey == 'n':
                    dQuery['query'] = 'n'
                    dQuery['qualifier'] = int(value)
                # today's entries
                elif sKey == 'today':
                    dQuery['query'] = 'today'
                    dQuery['qualifier'] = ''
                # entries for a particular date
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
                    dQuery['query'] = 'date'
                    dQuery['qualifier'] = sDate
        
        # extract the date column - it's used by most query types
        sDateCol = sRoomCol = ''
        for col in self.__conf['columns']:
            if 'date' in col.lower():
                sDateCol = col
            if 'room' in col.lower():
                sRoomCol = col
        if bDebug:
            print "-d- Columns of interest:\n-d- date: {}\n-d- room: {}".format(sDateCol, sRoomCol)
        
        sRoomQuery = 'WHERE '
        if dQuery['room'] != '*':
            sRoomQuery += '{}={} AND'.format(sRoomCol, dQuery['room'])
            
        if bDebug:
            print "-d- dQuery = {}".format(dQuery)
            print "-d- sRoomQuery = {}".format(sRoomQuery)
            
        # construct query
        if dQuery['query'] == 'n':
            # special case for the room query
            # 1) no ' and' at the end if a room WAS specified, and
            # 2) if a room wasn't specified, just delete the whole thing (no need for 'WHERE')
            sRoomQuery = sRoomQuery.replace(' AND', '') if dQuery['room'] != '*' else ''
            dbcmd = "SELECT * FROM {0} {1} ORDER BY ID DESC LIMIT {2}".format(self.__conf['table'], sRoomQuery, dQuery['qualifier'])
        elif dQuery['query'] == 'today':
            dbcmd = "SELECT * FROM {0} {1} {2} BETWEEN CURRENT_DATE() AND NOW() ORDER BY ID DESC".format(self.__conf['table'], sRoomQuery, sDateCol)
        elif dQuery['query'] == 'date':
            dbcmd = "SELECT * FROM {0} {1} {2} BETWEEN '{3}' AND '{3} 23:59:59' ORDER BY ID DESC".format(self.__conf['table'], sRoomQuery, sDateCol, dQuery['qualifier'])
        if bDebug:
            print "-d- MySQL command:\n-d- %s" % (dbcmd)
    
        return dbcmd
    
    """ execute a command
        Inputs:
            sqlcmd - the sql command to execute
            t - type of command to run. Valid values are 'insert' and 'select'
        Returns:
            nothing
    """
    def execute(self, sqlcmd, t='insert'):
        with self.db:
            self.curs.execute(sqlcmd)
        if 'select' in t.lower():
            self.dataRaw = self.curs.fetchall()
        
    """ Format retrieved data
        Inputs:
            none
        Returns:
            nothing
    """
    def formatResults(self):
        if self.dataRaw != []:
            self.dataFormatted = []
            self.dataFormatted.append("----------------------------------------------------------")
            self.dataFormatted.append("Date       | Time     | Room     | Temperature | Humidity")
            self.dataFormatted.append("----------------------------------------------------------")
            for i in reversed(xrange(len(self.dataRaw))):
                reading = self.dataRaw[i]
                date = "{}".format(reading[0])
                time = "{0:8s}".format(reading[1])
                room = "{0:8s}".format(reading[2])
                temp = "{0:11.1f}".format(reading[3])
                humi = "{0:0.1f}".format(reading[4]) + "%"
                self.dataFormatted.append( date + " | " + time + " | " + room + " | " + temp + " | " + humi )
            self.dataFormatted.append("----------------------------------------------------------")
        else:
            self.dataFormatted = "rawData is empty. Didn't format anything."
        
    """ Wrapper for constructing and executing a query in one go
        Inputs:
            sQuery - the type of query to execute
            bDebug - (optional) flag to print more info to console
        Returns:
            nothing
    """
    def retrieveData(self, sQuery, bDebug=False):
        dbcmd = self.constructQuery(sQuery, bDebug)
        self.executeQuery(dbcmd, 'select')
        
    """ Display formatted results in console
        Inputs:
            none
        Returns:
            nothing
    """
    def displayResults(self):
        self.formatResults()
        for line in self.dataFormatted:
            print line
            
    """ Insert data into the database
        Inputs:
            dData - dict of data with keys 'temperature' and 'humidity'
        Returns:
            True if data insertion was successful, false otherwise
    """
    def insertData(self, dData, bDebug=False):
        sColumns = ', '.join(self.__conf['columns'])
        self.dbcmd = "INSERT INTO {0} ({1}) values(CURRENT_DATE(), NOW(), '{2}', {3:0.1f}, {4:0.1f})".format(self.__conf['table'], sColumns, self.__conf['room'], dData['temperature'], dData['humidity'])
        if bDebug:
            print "-d- Insertion Command:\n\t{}".format(self.dbcmd)
        else:
            try:
                self.execute(self.dbcmd, 'insert')
            except Exception as E:
                print "-E- HomeDB Error: Some exception while trying to insert data into db."
                traceback.print_exc()
                return False
        return True
        
