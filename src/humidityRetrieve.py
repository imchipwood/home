#!/usr/bin/python
import sys
import os
import argparse
import traceback

sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/db")
from db_humidity import DBHumidity

parser = argparse.ArgumentParser()
parser.add_argument('-query',
                    '-q',
                    type=str,
                    default='',
                    help="Type of query - how and what data to be displayed")
parser.add_argument('-debug',
                    '-d',
                    action="store_true",
                    help="Enable debug messages")

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
    sDBAccessFileName = 'sql_humidity_get.txt'

    # set up db
    sHomeDBPath = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
    sDBCredentialsFile = sHomeDBPath+'/conf/'+sDBAccessFileName
    if bDebug:
        print "-d- Accessing DB using credentials found here:"
        print "-d- {}".format(sDBCredentialsFile)
    hdb = DBHumidity(sDBCredentialsFile, bDebug=bDebug)

    # do query and format the data
    try:
        hdb.retrieveData(sQuery, bDebug)
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
