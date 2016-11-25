"""Home Database

Handles general access to database.
Child classes must define construction of DB query strings and
formatting of data for printing
"""

import os
import MySQLdb
import traceback
from abc import abstractmethod


class DBHome(object):
    db = ""
    curs = ""
    dbcmd = ""
    dataRaw = []
    dataFormatted = []

    __conf = {"host": "",
              "db": "",
              "table": "",
              "user": "",
              "pw": "",
              "room": "",
              "columns": []
              }
    lDataColumns = []
    sConfFile = ""

    bDebug = False

    """Initialize database access

    Parse config file, connect to DB, set up cursor

    Inputs:
        f - full path to config file to parse
        bDebug - (Optional) boolean to enable debug messages
    """
    def __init__(self, f, bDebug=False):
        super(DBHome, self).__init__()

        self.bDebug = bDebug
        # read config file
        if os.path.exists(f):
            self.sConfFile = f
        else:
            print "-E- HomeDB: Check if file exists: {}".format(f)
            raise IOError()

        if self.readConfig():
            # open up database
            # if self.bDebug:
            #     print self.__conf
            try:
                self.db = MySQLdb.connect(host=self.__conf["host"],
                                          user=self.__conf["user"],
                                          passwd=self.__conf["pw"],
                                          db=self.__conf["db"])
                # http://www.neotitans.com/resources/python/mysql-python-connection-error-2006.html
                self.db.ping(True)
                self.curs = self.db.cursor()

                # figure out what data columns are available
                for col in self.__conf["columns"]:
                    if col not in ["tdate", "ttime", "room"]:
                        self.lDataColumns.append(col)

            except Exception as e:
                print "-E- HomeDB Error: Failed to open database"
                print e
                raise e
        else:
            print "-E- HomeDB Error: Failed to parse DB config file:"
            print "\t-E- {}".format(self.sConfFile)
            raise IOError

###############################################################################

#    """Format retrieved data
#
#    Inputs:
#        none
#    Returns:
#        nothing
#    """
#    @abstractmethod
#    def formatResults(self):
#        """ Format results into a readable/printable format """

    """Validate data before inserting into database

    Inputs:
        dData - dict of data with keys "temperature" and "humidity"
    Returns:
        True if data is valid, False otherwise
    """
    @abstractmethod
    def validateData(self, dData, bDebug=False):
        """ Validate data before inserting """

###############################################################################

    """Format retrieved data

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
            sHeader = "Date       | Time     | Room     | "
            for col in self.lDataColumns:
                sHeader += "{0:>12} | ".format(col)
            sHeader = sHeader[:-3]

            dataFormatted.append(sSeparator)
            dataFormatted.append(sHeader)
            dataFormatted.append(sSeparator)
            
            
            for i in reversed(xrange(len(self.getDataRaw()))):
                reading = self.getDataRaw()[i]
                date = "{}".format(reading[0])
                time = "{0:8s}".format(reading[1])
                room = "{0:8s}".format(reading[2])
                sInfo = "{} | {} | {}".format(date, time, room)
                lData = []
                for r in reading[3:]:
                    lData.append("{0:>12}".format(r))
                sData = ""
                for d in lData:
                    sData += " | {}".format(d)
                sData = sInfo + sData
                dataFormatted.append(sData)
            dataFormatted.append(sSeparator)
        else:
            dataFormatted = []
        return dataFormatted

###############################################################################

    """Construct a query based on string input

    Inputs:
        sQuery - the query as a string.
            Valid query options:
                n=<number> - get sthe last <number> entries
                today - get all entries from today
                room=<room> - pull data only from <room>
                date=<year>-<month>-<day> - get all entries for a
                    particular date where year is a 4 digit #
                    and month/day are 2 digits
            Default query if no options are specified - "n=5 room=*"
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
        sDateCol = sRoomCol = ""
        for col in self.__conf["columns"]:
            if "date" in col.lower():
                sDateCol = col
            if "room" in col.lower():
                sRoomCol = col
        if bDebug:
            print "-d- DBHome: Columns of interest:"
            print "-d- DBHome: date: {}".format(sDateCol)
            print "-d- DBHome: room: {}".format(sRoomCol)

        sRoomQuery = "WHERE"
        if dQuery["room"] != "*":
            if bDebug:
                print "-d- DBHome: room query: {}".format(dQuery["room"])
            lRooms = dQuery["room"].split(",")
            if len(lRooms) == 1:
                sRoomQuery += " {}={} AND".format(sRoomCol, lRooms[0])
            else:
                lRoomQueries = []
                for room in lRooms:
                    lRoomQueries.append(" {}={}".format(sRoomCol, room))
                for q in lRoomQueries[:-1]:
                    sRoomQuery += q + " AND"
                sRoomQuery += lRoomQueries[-1] + " AND"

        if bDebug:
            print "-d- DBHome: dQuery = {}".format(dQuery)
            print "-d- DBHome: sRoomQuery = {}".format(sRoomQuery)

        # construct query
        dbcmd = ""
        sColumns = ""
        for col in self.__conf["columns"]:
            sColumns += "{},".format(col)
        sColumns = sColumns[:-1]
        if dQuery["query"] == "n":
            # special case for the room query
            # 1) no " and" at the end if a room WAS specified, and
            # 2) if a room wasn't specified, just delete the
            #    whole thing (no need for "WHERE")
            if dQuery["room"] != "*":
                sRoomQuery = sRoomQuery.replace(" AND", "")
            else:
                sRoomQuery = ""
            dbcmd = (
                "SELECT {3} FROM {0} {1} ORDER BY ID DESC LIMIT {2}".format(
                    self.__conf["table"],
                    sRoomQuery,
                    dQuery["qualifier"],
                    sColumns
                )
            )
        elif dQuery["query"] == "today":
            dbcmd = (
                "SELECT {3} FROM {0} {1} {2} BETWEEN CURRENT_DATE() AND NOW() "
                "ORDER BY ID DESC".format(
                    self.__conf["table"],
                    sRoomQuery,
                    sDateCol,
                    sColumns
                )
            )
        elif dQuery["query"] == "yesterday":
            dbcmd = (
                "SELECT {3} FROM {0} {1} {2} BETWEEN CURRENT_DATE()-1 AND "
                "CURRENT_DATE()-1 ORDER BY ID DESC".format(
                    self.__conf["table"],
                    sRoomQuery,
                    sDateCol,
                    sColumns
                )
            )
        elif dQuery["query"] == "date":
            dbcmd = (
                "SELECT {4} FROM {0} {1} {2} BETWEEN '{3}' AND '{3} 23:59:59' "
                "ORDER BY ID DESC".format(
                    self.__conf["table"],
                    sRoomQuery,
                    sDateCol,
                    dQuery["qualifier"],
                    sColumns
                )
            )
        elif dQuery["query"] == "daterange":
            dbcmd = (
                "SELECT {5} FROM {0} {1} {2} BETWEEN '{3}' AND '{4} 23:59:59' "
                "ORDER BY ID DESC".format(
                    self.__conf["table"],
                    sRoomQuery,
                    sDateCol,
                    dQuery["qualifier"]["start"],
                    dQuery["qualifier"]["end"],
                    sColumns
                )
            )
        else:
            print "-E- DBHome: didn't recognize query type"
        if bDebug:
            print "-d- DBHome: MySQL command:\n-d- %s" % (dbcmd)
        return dbcmd

###############################################################################

    """Deconstruct the input args into a dictionary of options

    Inputs:
        None
    Returns:
        Nothing
    """
    def parseInputs(self, bDebug=False):
        if self.bDebug:
            bDebug = True

        if bDebug:
            print "-d- DBHome: Parsing query: '{}'".format(self.sQuery)

        # default query if no args are specified (or if empty args specified)
        dQuery = {}
        dQuery["query"] = "n"
        dQuery["qualifier"] = "8"  # 2 hours of data
        dQuery["room"] = "*"

        lArgs = self.sQuery.rstrip().lstrip().split(" ")
        if bDebug:
            print "-d- DBHome: args split into: '{}'".format(lArgs)
        # are they any args? If so, parse em. If not, assume default
        if len(lArgs) > 0 and lArgs != [""]:
            # loop thru each arg, populating the dQuery dictionary as we go
            for sArg in lArgs:
                # first, deconstruct the arg into a key/value pair
                sKey = value = ""
                sArgSplit = sArg.split("=")
                if len(sArgSplit) == 2:
                    sKey = sArgSplit[0].lower()
                    value = sArgSplit[1]
                elif len(sArgSplit) == 1:
                    sQ = sArgSplit[0].lower()
                    if sQ == "today" or sQ == "yesterday":
                        sKey = sQ
                        value = ""
                    else:
                        sKey = "n"
                        value = sArgSplit[0]
                else:
                    sException = ("-E- DBHome: Query args error."
                                  "Couldn't split them into a key/value pair"
                                  "\n\tArgs: {0}"
                                  "\n\tFailed on: {1}".format(sQuery, sArg))
                    raise Exception(sException)
                if bDebug:
                    print "-d- key, value: ({}, {})".format(sKey, value)

                # room specification
                if sKey == "room":
                    dQuery["room"] = "'{}'".format(value)
                # nEntries
                elif sKey == "n":
                    dQuery["query"] = "n"
                    try:
                        dQuery["qualifier"] = int(value)
                    except:
                        raise IOError("-E- DBHome: 'n' query invalid")
                # today's entries
                elif sKey == "today":
                    dQuery["query"] = "today"
                    dQuery["qualifier"] = ""
                # yesterday's entries
                elif sKey == "yesterday":
                    dQuery["query"] = "yesterday"
                    dQuery["qualifier"] = ""
                # entries for a particular date
                elif sKey == "date":
                    # check syntax of date
                    self.__verifyDateFormat(value)
                    dQuery["query"] = "date"
                    dQuery["qualifier"] = value
                elif sKey == "daterange":
                    sDateBeg = value.split(":")[0]
                    self.__verifyDateFormat(sDateBeg)
                    sDateEnd = value.split(":")[1]
                    self.__verifyDateFormat(sDateEnd)
                    dQuery["query"] = "daterange"
                    dQuery["qualifier"] = {"start": sDateBeg, "end": sDateEnd}
        return dQuery

###############################################################################

    """Insert data into the database

    Inputs:
        dData - dict of data with keys "temperature" and "humidity"
    Returns:
        True if data insertion was successful, False otherwise
    """
    # @abstractmethod
    def insertData(self, dData, insert=True, bDebug=False):
        """ Insert data into the database """
        dataFormattedArray = []
        for key in dData:
            dataFormattedArray.append("{}, ".format(dData[key]))
        dataFormattedArray[-1] = dataFormattedArray[-1].replace(", ", "")
        sData = ""
        for s in dataFormattedArray:
            sData += s
        sColumns = ", ".join(self.__conf["columns"])
        self.dbcmd = (
            "INSERT INTO {0} ({1}) values(CURRENT_DATE(), NOW(), '{2}', "
            "{3})".format(self.__conf["table"],
                          sColumns,
                          self.__conf["room"],
                          sData)
        )
        if bDebug:
            print "-d- DBHome: Insert Command\n\t{}".format(self.dbcmd)
        if insert:
            try:
                if bDebug:
                    "-d- DBHome: attempting insertion"
                self.executeCmd(self.dbcmd, "insert")
            except Exception as E:
                print "-E- DBHome: Error while inserting data into db."
                traceback.print_exc()
                return False
        return True

###############################################################################

    """Read config file and get MySQL database info out of it

    Inputs:
        None
    Returns:
        True if config was parsed properly, False otherwise
    """
    def readConfig(self):
        confTemp = {}
        with open(self.sConfFile, "r") as inf:
            for line in inf:
                line = line.rstrip().split("=")
                if line[0] == "h":
                    confTemp["host"] = line[-1]
                # database
                if line[0] == "db":
                    confTemp["db"] = line[-1]
                # table
                if line[0] == "t":
                    confTemp["table"] = line[-1]
                # username
                if line[0] == "u":
                    confTemp["user"] = line[-1]
                # password
                if line[0] == "p":
                    confTemp["pw"] = line[-1]
                # room
                if line[0] == "r":
                    confTemp["room"] = line[-1]
                # columns to populate
                if line[0] == "c":
                    confTemp["columns"] = line[-1].split(",")
        # check for blanks
        validConf = "" not in [confTemp["db"],
                               confTemp["table"],
                               confTemp["user"],
                               confTemp["pw"],
                               confTemp["host"]
                               ]
        if not validConf:
            print "-E- HomeDB Error: Config file parameter error"
            print "-E- 'db', 'table', 'user', or 'pw'"
        validConf = "" not in confTemp["columns"]
        if not validConf:
            print "-E- HomeDB Error: Config file parameter error"
            print "-E- 'columns'"
        if "get" not in self.sConfFile.lower():
            validConf = "" not in [confTemp["room"]]
            if not validConf:
                print "-E- HomeDB Error: Config file parameter error"
                print "-E- 'room'"
        if validConf:
            self.__conf = confTemp
        return validConf

###############################################################################

    """execute a command

    Inputs:
        sqlcmd - the sql command to execute
        t - type of command to run. Valid values are "insert" and "select"
    Returns:
        nothing
    """
    def executeCmd(self, cmd, t="insert"):
        with self.db:
            self.curs.execute(cmd)
        if "select" in t.lower():
            self.dataRaw = self.curs.fetchall()

###############################################################################

    """Wrapper for constructing and executing a query in one go

    Inputs:
        sQuery - the type of query to execute
        bDebug - (optional) flag to print more info to console
    Returns:
        nothing
    """
    def retrieveData(self, sQuery, bDebug=False):
        self.dbcmd = self.constructQuery(sQuery, bDebug)
        self.executeCmd(self.dbcmd, "select")

###############################################################################

    """Display formatted results in console

    Inputs:
        none
    Returns:
        nothing
    """
    def displayResults(self):
        self.dataFormatted = self.formatResults()
        for line in self.dataFormatted:
            print line

###############################################################################

    """return raw data array

    Inputs:
        none
    Returns:
        raw data array
    """
    def getDataRaw(self):
        return self.dataRaw

###############################################################################

    """return formatted data array

    Inputs:
        none
    Returns:
        formatted data array
    """
    def getDataFormatted(self):
        return self.dataFormatted
