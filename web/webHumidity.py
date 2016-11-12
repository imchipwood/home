#!/usr/bin/env python

import cgi
import cgitb
import os
import argparse
import traceback
import sys
sHomePath = "/home/cpw/dev/home"
sys.path.append(sHomePath+"/lib/db")
from db_humidity import DBHumidity

parser = argparse.ArgumentParser()
parser.add_argument('-room',
                    '-r',
                    type=str,
                    default='media',
                    help="Room to get data from. Default='media'")
parser.add_argument('-debug',
                    '-d',
                    action="store_true",
                    help="Enable debug messages")

global sRoom
global bDebug
args = parser.parse_args()
sRoom = args.room
bDebug = args.debug


# print an HTTP header
def printHTTPheader():
    print "Content-type: text/html"
    print ""
    print ""


def printHTMLhead(sTitle):
    print "<html>"
    print "    <head>"
    print "        <title>{}</title>".format(sTitle)
    print "    </head>"


# viewWindowMode: 'explicit', viewWindow:{ max=100, min=0}
def printChartCode(table, sRooms):
    # this string contains the web page that will be served
    try:
        # convert string of rooms into list
        lRooms = [room for room in sRooms.split(',')]

        # Are we displaying data from multiple rooms?
        columnHeaders = "['Date', "
        if len(lRooms) > 1:
            for room in lRooms:
                columnHeaders += "'{} Temperature', '{} Humidity'".format(room)
            roomStr = ""
        else:
            columnHeaders += "'Temperature', 'Humidity'"
            roomStr = " in all rooms"
            if lRooms[0] != '*':
                roomStr = " in {} room".format(lRooms[0])
        columnHeaders += "]"
        page_str = """
    <body>
    <h1>Raspberry Pi Humidity/Temperature Logger</h1>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        <!--var data = google.visualization.arrayToDataTable([ ['Date', 'Temperature', 'Humidity'],-->
        var data = google.visualization.arrayToDataTable([ %s,
%s ]);

        var options = {
          title: 'Temperature/Humidity measurements for last 24 hours%s',
          hAxis: { title: 'Date', titleTextStyle: {color: 'blue'}, showTextEvery: 8,
                   slantedText: true, slantedTextAngle: 90
                 },
          vAxes: {
                  0: { title: 'Temperature in F', titleTextStyle: {color: 'red'} },
                  1: { title: '%% Humidity', titleTextStyle: {color: 'blue'}, format:"#%%" }
                 },
          colors: ['red', 'blue'],
          series: { 0: {targetAxisIndex:0},
                    1: {targetAxisIndex:1}
                  }
        };

        var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
        chart.draw(data, options);
      }
    </script>
    <div id="chart_div" style="width: 900px; height: 500px;"></div>
    </body>""" % (columnHeaders, table, roomStr)
    except:
        print "-E- failed to create page_str"
        return

    print page_str


def main():
    global sRoom
    global sHomePath
    # enable tracebacks of exceptions
    cgitb.enable()

    # user-defined args
    sDBAccessFileName = 'sql_humidity_get.txt'

    # set up db
    sDBCredentialsFile = sHomePath+"/conf/"+sDBAccessFileName
    hdb = DBHumidity(sDBCredentialsFile, bDebug=False)

    printHTTPheader()
    printHTMLhead("Raspberry Pi Humidity/Temperature Tracker")

    # do query and format the data
    try:
        # pull 24 hours of data
        hdb.retrieveData('n=96 room={}'.format(sRoom), bDebug=False)
        # convert to a format Google Charts can work with
        chartTable = hdb.formatDataForGoogleCharts()
        printChartCode(chartTable, sRoom)
    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e

    print "</html>"
    return

if __name__ == "__main__":
    main()
