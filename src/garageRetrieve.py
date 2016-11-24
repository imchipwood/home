#!/usr/bin/python
import sys
import os
import argparse
import traceback

sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../lib/db")
from db_home import DBHome


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-query',
                        '-q',
                        type=str,
                        default='',
                        help="Type of query - how and what data to be displayed")
    parser.add_argument("-configFile",
                        "-c",
                        type=str,
                        default="sql_doors_get.txt",
                        help="Config file for SQL database interaction")
    parser.add_argument('-debug',
                        '-d',
                        action="store_true",
                        help="Enable debug messages")

    args = parser.parse_args()
    return args


def main():
    parsedArgs = parseArgs()
    sQuery = parsedArgs.query
    sDBAccessFileName = parsedArgs.configFile
    bDebug = parsedArgs.debug
    if bDebug:
        print "-d- args:"
        print "-d- sQuery: {}".format(sQuery)

    # set up db
    sHomeDBPath = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
    sDBCredentialsFile = sHomeDBPath+'/conf/'+sDBAccessFileName
    if bDebug:
        print "-d- Accessing DB using credentials found here:"
        print "-d- {}".format(sDBCredentialsFile)
    hdb = DBHome(sDBCredentialsFile, bDebug=bDebug)

    # do query and format the data
    try:
        hdb.retrieveData(sQuery, bDebug)
        hdb.getDataRaw()
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
