import traceback
from db_home import DBHome

""" Humidity Database
    Contains specifics for database interaction
    for humidity sensors.
"""
class DBHumidity(DBHome):

    sQuery = ''

    def __init__(self, f, bDebug=False):
        super(DBHumidity, self).__init__(f, bDebug)

####################################################################################################

    """ Deconstruct the input args into a dictionary of options
    """
    def parseInputs(self, bDebug=False):

        if self.bDebug:
            bDebug = True

        if bDebug:
            print '-d- Parsing query: "{}"'.format(self.sQuery)

        # default query if no args are specified (or if empty args specified)
        dQuery = {}
        dQuery['query']     = 'n'
        dQuery['qualifier'] = '5'
        dQuery['room']      = '*'

        lArgs = self.sQuery.rstrip().lstrip().split(' ')
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
                    sKey    = sArgSplit[0].lower()
                    value   = sArgSplit[1]
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
                    dQuery['query']     = 'n'
                    dQuery['qualifier'] = int(value)
                # today's entries
                elif sKey == 'today':
                    dQuery['query']     = 'today'
                    dQuery['qualifier'] = ''
                # entries for a particular date
                elif sKey == 'date':
                    # check syntax of date
                    sDate       = value
                    sDateSplit  = sDate.split('-')
                    dDate       = {'year':sDateSplit[0], 'month':sDateSplit[1], 'day':sDateSplit[2]}
                    if len(dDate['year']) != 4:
                        raise Exception('-E- Date entered incorrectly - check the year, should be 4 digits.\n\tYear: {}'.format(dDate['year']))
                    if len(dDate['month']) != 2:
                        raise Exception('-E- Date entered incorrectly - check the month, should be 2 digits.\n\tMonth: {}'.format(dDate['month']))
                    if len(dDate['day']) != 2:
                        raise Exception('-E- Date entered incorrectly - check the day, should be 2 digits.\n\tDay: {}'.format(dDate['day']))
                    dQuery['query'] = 'date'
                    dQuery['qualifier'] = sDate

        return dQuery

####################################################################################################

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
    def constructQuery(self, sQ, bDebug=False):

        if self.bDebug:
            bDebug = True

        self.sQuery = sQ
        dQuery = parseInputs(bDebug)

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

####################################################################################################

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

####################################################################################################

    """ Insert data into the database
        Inputs:
            dData - dict of data with keys 'temperature' and 'humidity'
        Returns:
            True if data insertion was successful, false otherwise
    """
    def insertData(self, dData, bDebug=False):

        if self.bDebug:
            bDebug = True

        sColumns = ', '.join(self.__conf['columns'])
        self.dbcmd = "INSERT INTO {0} ({1}) values(CURRENT_DATE(), NOW(), '{2}', {3:0.1f}, {4:0.1f})".format(self.__conf['table'], sColumns, self.__conf['room'], dData['temperature'], dData['humidity'])
        if bDebug:
            print "-d- Insertion Command:\n\t{}".format(self.dbcmd)
        else:
            try:
                self.executeCmd(self.dbcmd, 'insert')
            except Exception as E:
                print "-E- HomeDB Error: Some exception while trying to insert data into db."
                traceback.print_exc()
                return False
        return True
