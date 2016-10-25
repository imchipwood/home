#!/usr/bin/python
import sys 
import os
import argparse
import traceback


sys.path.append('/home/pi/dev/home/lib/db')
from HomeDB import HomeDB

parser = argparse.ArgumentParser()
parser.add_argument('-query', '-q', type=str, default='', help="Type of query - how and what do you want data displayed")
parser.add_argument('-debug', '-d', action="store_true", help="Prevent updates to SQL database, while also printing extra stuff to console. Optional")

args = parser.parse_args()
global sQuery
global bDebug
sQuery = args.query
bDebug = args.debug
if bDebug:
    print "-d- args:"
    print "-d- sQuery: {}".format(sQuery)

def main():
    global sQuery
    global bDebug

    # user-defined args
    sSQLAccessFileName = 'sqlget.txt'

    # set up SQL db
    sSQLCredentialsFile = os.path.dirname(os.path.realpath(__file__))+'/../conf/'+sSQLAccessFileName
    if bDebug:
        print "-d- Accessing SQL DB using credentials found here:"
        print "-d- {}".format(sSQLCredentialsFile)
    hdb = HomeDB(sSQLCredentialsFile)
    
    # do SQL query and format the data
    try:
        hdb.command(sQuery)
        hdb.displayResults()
    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e
    return True


if __name__ == '__main__':
    main()
