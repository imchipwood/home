#!/usr/bin/python

import cgi
import cgitb
import os
import argparse
import traceback
import sys
sHomePath = "/home/cdub/dev/home"
sys.path.append(sHomePath+"/lib/db")
from db_home import DBHome
from db_humidity import DBHumidity

parser = argparse.ArgumentParser()
parser.add_argument('-debug',
                    '-d',
                    action="store_true",
                    help="Enable debug messages")

global bDebug
args = parser.parse_args()
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
    <h1>Humidity/Temperature</h1>
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
          hAxis: { title: 'Date',
                   titleTextStyle: {color: 'blue'},
                   showTextEvery: 8,
                   slantedText: true,
                   slantedTextAngle: 45
          },
          vAxes: {
                  0: { title: 'Temperature in F',
                       titleTextStyle: {color: 'red'} },
                  1: { title: '%% Humidity',
                       titleTextStyle: {color: 'blue'},
                       format:"#%%" }
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
    <div id="chart_div" style="width: 900px; height: 500px;"></div>""" % (columnHeaders, table, roomStr)
    except:
        print "-E- failed to create page_str"
        return

    print page_str


def main():
    global sHomePath
    global bDebug
    # enable tracebacks of exceptions
    cgitb.enable()

    # check for http args
    form = cgi.FieldStorage()
    sQuery = form.getvalue("query")
    if sQuery is None:
        sQuery = "n=96"
    sRoom = form.getvalue("room")
    if sRoom is None:
        sRoom = "media"

    # user-defined args
    sDBAccessFileName = "sql_humidity_get.txt"
    sDBDoorsFileName = "sql_doors_get.txt"

    # set up db
    sDBCredentialsFile = sHomePath+"/conf/"+sDBAccessFileName
    hdb = DBHumidity(sDBCredentialsFile, bDebug)

    sDBDoorsFile = sHomePath+"/conf/"+sDBDoorsFileName
    ddb = DBHome(sDBDoorsFile, bDebug)

    printHTTPheader()
    printHTMLhead("Home Monitor")
    print "    <body>"

    # do query and format the data
    try:
        # get garage door status
        ddb.retrieveData("n=1 room=garage", bDebug)
        state = ddb.getDataRaw()[-1][-1]
        if state == 0:
            state = "closed"
        elif state == 50:
            state = "moving"
        elif state == 100:
            state = "open"
        print "<h1>Garage Door is: {}</h1>".format(state)
        # make a refresh button
        print """<FORM><INPUT TYPE="button" onClick="history.go(0)" VALUE="Refresh"></FORM>"""

        # pull 24 hours of data
        hdb.retrieveData('{} room={}'.format(sQuery, sRoom), bDebug)
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

    print "    </body>"
    print "</html>"
    return

if __name__ == "__main__":
    main()
