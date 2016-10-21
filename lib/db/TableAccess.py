# SQL Library
#
# The intention of this file is to consolidate all 
# SQL interactions into a single library,
# thereby de-cluttering the scripts coordinating
# sensor reading, data logging, etc.

import os

class TableAccess(object):
    sDB = ''
    sTable = ''
    sUser = ''
    sPW = ''
    sRoom = ''
    lColumns
    sFile = ''
    
    def __init__(self, file):
        super(TableAccess, self).__init__()
        if os.path.exists(file):
            self.sFile = file
        else:
            raise IOError('-E- SQLReader: Error attempting to open {} for table info retrieval.\nPlease check if the file exists'.format(file))
        self.readFile()

    def readFile(self):
        with open(self.sFile, 'r') as inf:
            for line in inf:
                line = line.rstrip().split('=')
                # database
                if line[0] == 'db':
                    self.sDB = line[-1]
                # table
                if line[0] == 't':
                    self.sTable = line[-1]
                # username
                if line[0] == 'u':
                    self.sUser = line[-1]
                # password
                if line[0] == 'p':
                    self.sPW = line[-1]
                # room
                if line[0] == 'r':
                    self.sRoom = line[-1]
                # columns to populate
                if line[0] == 'c':
                    self.lColumns = line[-1].split[',']
        assert not '' in [self.sDB, self.sTable, self.sUser, self.sPW]
        if not 'get' in self.sFile.lower():
            assert not '' in [self.sRoom]
            for col in self.lColumns:
                assert not '' in col
        
    def getInfo(self):
        return {'db':self.sDB, 'table':self.sTable, 'user':self.sUser, 'pw':self.sPW, 'room':self.sRoom, 'columns':self.lColumns}

