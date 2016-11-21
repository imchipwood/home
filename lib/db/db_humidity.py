"""Humidity Database

Contains specifics for database interaction for humidity sensors.
"""

import traceback
from db_home import DBHome


class DBHumidity(DBHome):
    sQuery = ''

    def __init__(self, f, bDebug=False):
        super(DBHumidity, self).__init__(f, bDebug)

###############################################################################

    """ Construct a query based on string input
        Inputs:
            sQuery - the query as a string.
                Valid query options:
                    n=<number> - get the last <number> entries
                    today - get all entries from today
                    room=<room> - pull data only from <room>
                    date=<year>-<month>-<day> - get all entries for a
                        particular date where year is a 4 digit #
                        and month/day are 2 digits
                Default query if no options are specified - 'n=5 room=*'
            bDebug - (optional) flag to print more info to console
        Returns:
            SQL command as a string
    """
    def constructQuery(self, sQ, bDebug=False):
        if self.bDebug:
            bDebug = True

        self.sQuery = sQ
        dQuery = self.parseInputs(bDebug)

        # extract the date column - it's used by most query types
        sDateCol = sRoomCol = ''
        for col in self._DBHome__conf['columns']:
            if 'date' in col.lower():
                sDateCol = col
            if 'room' in col.lower():
                sRoomCol = col
        if bDebug:
            print "-d- DBHumidity: Columns of interest:"
            print "-d- DBHumidity: date: {}".format(sDateCol)
            print "-d- DBHumidity: room: {}".format(sRoomCol)

        sRoomQuery = 'WHERE'
        if dQuery['room'] != '*':
            if bDebug:
                print "-d- DBHumidity: room query: {}".format(dQuery['room'])
            lRooms = dQuery['room'].split(',')
            if len(lRooms) == 1:
                sRoomQuery += ' {}={} AND'.format(sRoomCol, lRooms[0])
            else:
                lRoomQueries = []
                for room in lRooms:
                    lRoomQueries.append(' {}={}'.format(sRoomCol, room))
                for q in lRoomQueries[:-1]:
                    sRoomQuery += q + ' AND'
                sRoomQuery += lRoomQueries[-1] + ' AND'

        if bDebug:
            print "-d- DBHumidity: dQuery = {}".format(dQuery)
            print "-d- DBHumidity: sRoomQuery = {}".format(sRoomQuery)

        # construct query
        dbcmd = ''
        if dQuery['query'] == 'n':
            # special case for the room query
            # 1) no ' and' at the end if a room WAS specified, and
            # 2) if a room wasn't specified, just delete the
            #    whole thing (no need for 'WHERE')
            if dQuery["room"] != "*":
                sRoomQuery = sRoomQuery.replace(" AND", "")
            else:
                sRoomQuery = ""
            dbcmd = (
                "SELECT * FROM {0} {1} ORDER BY ID DESC LIMIT {2}".format(
                    self._DBHome__conf['table'],
                    sRoomQuery,
                    dQuery['qualifier']
                )
            )
        elif dQuery['query'] == 'today':
            dbcmd = (
                "SELECT * FROM {0} {1} {2} BETWEEN CURRENT_DATE() AND NOW() "
                "ORDER BY ID DESC".format(
                    self._DBHome__conf['table'],
                    sRoomQuery,
                    sDateCol
                )
            )
        elif dQuery['query'] == 'yesterday':
            dbcmd = (
                "SELECT * FROM {0} {1} {2} BETWEEN CURRENT_DATE()-1 AND "
                "CURRENT_DATE()-1 ORDER BY ID DESC".format(
                    self._DBHome__conf['table'],
                    sRoomQuery,
                    sDateCol
                )
            )
        elif dQuery['query'] == 'date':
            dbcmd = (
                "SELECT * FROM {0} {1} {2} BETWEEN '{3}' AND '{3} 23:59:59' "
                "ORDER BY ID DESC".format(
                    self._DBHome__conf['table'],
                    sRoomQuery,
                    sDateCol,
                    dQuery['qualifier']
                )
            )
        elif dQuery['query'] == 'daterange':
            dbcmd = (
                "SELECT * FROM {0} {1} {2} BETWEEN '{3}' AND '{4} 23:59:59' "
                "ORDER BY ID DESC".format(
                    self._DBHome__conf['table'],
                    sRoomQuery,
                    sDateCol,
                    dQuery['qualifier']['start'],
                    dQuery['qualifier']['end']
                )
            )
        else:
            print "-E- DBHumidity: didn't recognize query type"
        if bDebug:
            print "-d- DBHumidity: MySQL command:\n-d- %s" % (dbcmd)
        return dbcmd

###############################################################################

    """ Deconstruct the input args into a dictionary of options
    """
    def parseInputs(self, bDebug=False):
        if self.bDebug:
            bDebug = True

        if bDebug:
            print '-d- DBHumidity: Parsing query: "{}"'.format(self.sQuery)

        # default query if no args are specified (or if empty args specified)
        dQuery = {}
        dQuery['query'] = 'n'
        dQuery['qualifier'] = '8'  # 2 hours of data
        dQuery['room'] = '*'

        lArgs = self.sQuery.rstrip().lstrip().split(' ')
        if bDebug:
            print '-d- DBHumidity: args split into: "{}"'.format(lArgs)
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
                    sQ = sArgSplit[0].lower()
                    if sQ == 'today' or sQ == 'yesterday':
                        sKey = sQ
                        value = ""
                    else:
                        sKey = "n"
                        value = sArgSplit[0]
                else:
                    sException = ("-E- DBHumidity: Query args error."
                                  "Couldn't split them into a key/value pair"
                                  "\n\tArgs: {0}"
                                  "\n\tFailed on: {1}".format(sQuery, sArg))
                    raise Exception(sException)
                if bDebug:
                    print "-d- key, value: ({}, {})".format(sKey, value)

                # room specification
                if sKey == "room":
                    dQuery['room'] = "'{}'".format(value)
                # nEntries
                elif sKey == "n":
                    dQuery['query'] = "n"
                    try:
                        dQuery['qualifier'] = int(value)
                    except:
                        raise IOError("-E- DBHumidity: 'n' query value invalid")
                # today's entries
                elif sKey == "today":
                    dQuery['query'] = "today"
                    dQuery['qualifier'] = ""
                # yesterday's entries
                elif sKey == "yesterday":
                    dQuery['query'] = "yesterday"
                    dQuery['qualifier'] = ""
                # entries for a particular date
                elif sKey == "date":
                    # check syntax of date
                    self.__verifyDateFormat(value)
                    dQuery['query'] = "date"
                    dQuery['qualifier'] = value
                elif sKey == "daterange":
                    sDateBeg = value.split(":")[0]
                    self.__verifyDateFormat(sDateBeg)
                    sDateEnd = value.split(":")[1]
                    self.__verifyDateFormat(sDateEnd)
                    dQuery['query'] = "daterange"
                    dQuery['qualifier'] = {'start': sDateBeg, 'end': sDateEnd}
        return dQuery

###############################################################################

    """ Format retrieved data
        Inputs:
            none
        Returns:
            nothing
    """
    def formatResults(self):
        if self.getDataRaw() != []:
            dataFormatted = []
            sSeparator = ("----------------------------"
                          "----------------------------")
            sHeader = ("Date       | Time     | Room     | Temperature | "
                       "Humidity")
            dataFormatted.append(sSeparator)
            dataFormatted.append(sHeader)
            dataFormatted.append(sSeparator)
            for i in reversed(xrange(len(self.getDataRaw()))):
                reading = self.getDataRaw()[i]
                date = "{}".format(reading[0])
                time = "{0:8s}".format(reading[1])
                room = "{0:8s}".format(reading[2])
                temp = "{0:11.1f}".format(reading[3])
                humi = "{0:0.1f}".format(reading[4]) + "%"
                sData = "{} | {} | {}".format(date, time, room)
                sData += " | {} | {}".format(temp, humi)
                dataFormatted.append(sData)
            dataFormatted.append(sSeparator)
        else:
            dataFormatted = []
        return dataFormatted

###############################################################################

    """Validate data to ensure no bad values are inserted into database
    Inputs:
        dData - dict of data with keys 'humidity' and 'temperature'
    Returns:
        True if data is valid, False otherwise
    """
    def __validateData(self, dData, bDebug=False):
        if 0 <= dData['humidity'] <= 100 and -100 <= dData['temperature'] <= 200:
            return True
        return False


###############################################################################

    """ Insert data into the database
        Inputs:
            dData - dict of data with keys 'temperature' and 'humidity'
        Returns:
            True if data insertion was successful, False otherwise
    """
    def insertData(self, dData, insert=True, bDebug=False):
        if self.bDebug:
            bDebug = True

        if self.__validateData(dData, bDebug):
            sColumns = ', '.join(self._DBHome__conf['columns'])
            # I hate long strings
            self.dbcmd = (
                "INSERT INTO {0} ({1}) values(CURRENT_DATE(), NOW(), '{2}', "
                "{3:0.1f}, {4:0.1f})".format(self._DBHome__conf['table'],
                                             sColumns,
                                             self._DBHome__conf['room'],
                                             dData['temperature'],
                                             dData['humidity'])
            )
            if bDebug:
                print "-d- DBHumidity: Insertion Command\n\t{}".format(self.dbcmd)
            if insert:
                try:
                    if bDebug:
                        "-d- DBHumidity: attempting insertion"
                    self.executeCmd(self.dbcmd, 'insert')
                    return True
                except Exception as E:
                    print "-E- DBHumidity: Error while inserting data into db."
                    traceback.print_exc()
                    return False
        else:
            if bDebug:
                print "-e- DBHumidity: Data invalid - check sensor connections"
            return False

###############################################################################

    """ Verify Date Format for queries
        private function to ensure SQL date queries are valid
        Inputs:
            sDate - date as a string 'year-month-day'
        Returns:
            Nothing - raises an exception if format is incorrect
    """
    def __verifyDateFormat(self, sDate):
        sDateSplit = sDate.split('-')
        dDate = {'year': sDateSplit[0],
                 'month': sDateSplit[1],
                 'day': sDateSplit[2]}
        valid = True
        if len(dDate['year']) != 4:
            print ("-E- DBHumidity: Date entered incorrectly -"
                   "year should be 4 digits. Year: {}".format(dDate['year']))
            valid = False
        if len(dDate['month']) != 2:
            print ("-E- DBHumidity: Date entered incorrectly -"
                   "month should be 2 digits. Month: {}".format(dDate['month']))
            valid = False
        if len(dDate['day']) != 2:
            print ("-E- DBHumidity: Date entered incorrectly -"
                   " day should be 2 digits. Day: {}".format(dDate['day']))
            valid = False
        return valid

###############################################################################

    """ Create Google Charts Javascript table
        Inputs:
            None
        Returns:
            dataFormatted - array of strings formatted for Google Charts
                Javascript: ['datetime', temperature, humidity]
    """
    # TODO: Handle formatting when multiple rooms have been requested
    def formatDataForGoogleCharts(self):
        dataFormatted = ""
        dataFormattedArray = []
        if self.getDataRaw() != []:
            # build all table rows
            for i in reversed(xrange(len(self.getDataRaw()))):
                reading = self.getDataRaw()[i]
                sDateTime = "{} {}".format(reading[0], reading[1])
                sTime = "{}".format(reading[1])   # time only
                sTemp = "{0:0.1f}".format(reading[3])
                sHumi = "{0:0.4f}".format(float(reading[4])/100.)
                sRow = "['{0}', {1}, {2}],\n".format(sTime, sTemp, sHumi)
                dataFormattedArray.append(sRow)

            # remove extra comma from final row
            dataFormattedArray[-1] = dataFormattedArray[-1].replace('],', ']')
            # convert array into string
            for line in dataFormattedArray:
                    dataFormatted += line
        return dataFormatted
