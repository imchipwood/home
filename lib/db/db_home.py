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
    db = ''
    curs = ''
    dbcmd = ''
    dataRaw = []
    dataFormatted = []

    __conf = {'host': '',
              'db': '',
              'table': '',
              'user': '',
              'pw': '',
              'room': '',
              'columns': []
              }
    sConfFile = ''

    bDebug = False

    """ Initialize database access
        Parse config file, connect to DB, set up cursor
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
            if self.bDebug:
                print self.__conf
            try:
                self.db = MySQLdb.connect(host=self.__conf['host'],
                                          user=self.__conf['user'],
                                          passwd=self.__conf['pw'],
                                          db=self.__conf['db'])
                self.curs = self.db.cursor()
            except Exception as e:
                print "-E- HomeDB Error: Failed to open database"
                print e
                raise IOError
        else:
            print "-E- HomeDB Error: Failed to parse DB config file:"
            print "\t-E- {}".format(self.sConfFile)
            raise IOError

###############################################################################

    """ Construct a query based on string input
        Inputs:
            sQuery - the query as a string.
            bDebug - (optional) flag to print more info to console
        Returns:
            DB command as a string
    """
    @abstractmethod
    def constructQuery(self, sQuery, bDebug=False):
        """Build a query based on inputs - Must return query as a string """

    """ Format retrieved data
        Inputs:
            none
        Returns:
            nothing
    """
    @abstractmethod
    def formatResults(self):
        """ Format results into a readable/printable format """

    """ Insert data into the database
        Inputs:
            dData - dict of data with keys 'temperature' and 'humidity'
        Returns:
            True if data insertion was successful, False otherwise
    """
    @abstractmethod
    def insertData(self, dData, bDebug=False):
        """ Insert data into the database """

    """ Validate data before inserting into database
        Inputs:
            dData - dict of data with keys 'temperature' and 'humidity'
        Returns:
            True if data is valid, False otherwise
    """
    @abstractmethod
    def validateData(self, dData, bDebug=False):
        """ Validate data before inserting """

###############################################################################

    """ Read config file and get MySQL database info out of it
        Inputs:
            None
        Returns:
            True if config was parsed properly, False otherwise
    """
    def readConfig(self):
        confTemp = {}
        with open(self.sConfFile, 'r') as inf:
            for line in inf:
                line = line.rstrip().split('=')
                if line[0] == 'h':
                    confTemp['host'] = line[-1]
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
        validConf = '' not in [confTemp['db'],
                               confTemp['table'],
                               confTemp['user'],
                               confTemp['pw'],
                               confTemp['host']
                               ]
        if not validConf:
            print "-E- HomeDB Error: Config file parameter error"
            print "-E- 'db', 'table', 'user', or 'pw'"
        validConf = '' not in confTemp['columns']
        if not validConf:
            print "-E- HomeDB Error: Config file parameter error"
            print "-E- 'columns'"
        if 'get' not in self.sConfFile.lower():
            validConf = '' not in [confTemp['room']]
            if not validConf:
                print "-E- HomeDB Error: Config file parameter error"
                print "-E- 'room'"
        if validConf:
            self.__conf = confTemp
        return validConf

###############################################################################

    """ execute a command
        Inputs:
            sqlcmd - the sql command to execute
            t - type of command to run. Valid values are 'insert' and 'select'
        Returns:
            nothing
    """
    def executeCmd(self, cmd, t='insert'):
        with self.db:
            self.curs.execute(cmd)
        if 'select' in t.lower():
            self.dataRaw = self.curs.fetchall()

###############################################################################

    """ Wrapper for constructing and executing a query in one go
        Inputs:
            sQuery - the type of query to execute
            bDebug - (optional) flag to print more info to console
        Returns:
            nothing
    """
    def retrieveData(self, sQuery, bDebug=False):
        self.dbcmd = self.constructQuery(sQuery, bDebug)
        self.executeCmd(self.dbcmd, 'select')

###############################################################################

    """ Display formatted results in console
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

    """ return raw data array
        Inputs:
            none
        Returns:
            raw data array
    """
    def getDataRaw(self):
        return self.dataRaw

###############################################################################

    """ return formatted data array
        Inputs:
            none
        Returns:
            formatted data array
    """
    def getDataFormatted(self):
        return self.dataFormatted
