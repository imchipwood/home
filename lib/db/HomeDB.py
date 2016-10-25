# SQL Library
#
# The intention of this file is to consolidate all 
# SQL interactions into a single library,
# thereby de-cluttering the scripts coordinating
# sensor reading, data logging, etc.

import os
import MySQLdb

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
        
    def constructQuery(self, sQuery):
        bDebug = True
        
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
    
    def executeQuery(self, sqlcmd):
        with self.db:
            self.curs.execute(sqlcmd)
        self.dataRaw = self.curs.fetchall()
        
    def formatResults(self):
        self.dataFormatted = []
        self.dataFormatted.append("\nDate       | Time     | Room     | Temperature | Humidity")
        self.dataFormatted.append( "----------------------------------------------------------")
        
        for i in reversed(xrange(len(self.dataRaw))):
            reading = self.dataRaw[i]
            date = "{}".format(reading[0])
            time = "{0:8s}".format(reading[1])
            room = "{0:8s}".format(reading[2])
            temp = "{0:11.1f}".format(reading[3])
            humi = "{0:0.1f}".format(reading[4]) + "%"
            self.dataFormatted.append( date + " | " + time + " | " + room + " | " + temp + " | " + humi )
        
    def command(self, sQuery):
        dbcmd = self.constructQuery(sQuery)
        self.executeQuery(dbcmd)
        
    def displayResults(self):
        self.formatResults()
        for line in self.dataFormatted:
            print line

