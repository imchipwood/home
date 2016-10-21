# SQL Library
#
# The intention of this file is to consolidate all 
# SQL interactions into a single library,
# thereby de-cluttering the scripts coordinating
# sensor reading, data logging, etc.

import os

class TableAccess(object):
    sTable = ''
    sUser = ''
    sPW = ''
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
                line = line.rstrip()
                if line[0] == 't':
                    self.sTable = line.split('=')[-1]
                if line[0] == 'u':
                    self.sUser = line.split('=')[-1]
                if line[0] == 'p':
                    self.sPW = line.split('=')[-1]
        assert not '' in [self.sTable, self.sUser, self.sPW]
        
    def getInfo(self):
        return {'table':self.sTable, 'user':self.sUser, 'pw':self.sPW}

