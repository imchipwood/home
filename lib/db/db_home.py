# Home Database
#
# Provides basic database connectivity

import os
import MySQLdb
import traceback
from abc import abstractmethod

""" Home Database
    Handles general access to database.
    Child classes must define construction of DB query strings and
    formatting of data for printing
"""
class DBHome(object):
    db = ''
    curs = ''
    dbcmd = ''
    dataRaw = []
    dataFormatted = []

    __conf = {'db':'', 'table':'', 'user':'', 'pw':'', 'room':'', 'columns':[]}
    sConfFile = ''
    
    bDebug = False
    
    """ Initialize database access
        Parse config file, connect to DB, set up cursor
    """
    def __init__(self, f, debug):
        super(DBHome, self).__init__()

        self.bDebug = debug
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

####################################################################################################

    """ Construct a query based on string input
        Inputs:
            sQuery - the query as a string.
            bDebug - (optional) flag to print more info to console
        Returns:
            DB command as a string
    """
    @abstractmethod
    def constructQuery(self, sQuery, bDebug=False):
        """Build a query based on inputs - Must return the query as a string """

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
            True if data insertion was successful, false otherwise
    """
    @abstractmethod
    def insertData(self, dData, bDebug=self.bDebug):
        """ Insert data into the database """

####################################################################################################

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

####################################################################################################

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

####################################################################################################

    """ Wrapper for constructing and executing a query in one go
        Inputs:
            sQuery - the type of query to execute
            bDebug - (optional) flag to print more info to console
        Returns:
            nothing
    """
    def retrieveData(self, sQuery, bDebug=self.bDebug):
        self.dbcmd = self.constructQuery(sQuery, bDebug)
        self.executeCmd(self.dbcmd, 'select')

####################################################################################################

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

