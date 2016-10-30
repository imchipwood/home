import sys
sys.path.append('/home/pi/dev/home/lib/db')
from db_humidity import DBHumidity

sRoom = 'media'
sDBAccessFileName = 'sqlget.txt'
sDBCredentialsFile = "/home/pi/dev/home/conf/" + sDBAccessFileName
hdb = DBHumidity(sDBCredentialsFile, bDebug=False)
hdb.retrieveData('n=96 room={}'.format(sRoom), bDebug=False)
hdb.getDataRaw()
