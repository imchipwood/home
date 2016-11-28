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
def printChartCode(table, sQuery, sRooms):
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
            # roomStr = " in all rooms"
            # if lRooms[0] != '*':
            #     roomStr = " in {} room".format(lRooms[0])
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
          title: 'Temperature/Humidity measurements for query="%s", room="%s"',
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
    <div id="chart_div" style="width: 900px; height: 500px;"></div>""" % (columnHeaders, table, sQuery, sRooms)
    except:
        print "-E- failed to create page_str"
        return

    print page_str


def chartOptions():
    # room choices
    print '<form action="/cgi-bin/webHome.py" method="post" target="_blank">/'
    print '<input type="checkbox" name="media" value="on" />media'
    print '<input type="checkbox" name="garage" value="on" />garage'
    print 'input type="radio" name="today" value="on" />today'
    print 'input type="rdaio" name="24hrs" value="on" />last 24 hours'
    print 'input type="radio" name="12hrs" value="on" />last 12 hours'
    print 'input type="radio" name="6hrs" value="on" />last 6 hours'
    print '<input type="submit" value="Execute Query" />'
    print '</form>'

def dprint(s):
    print "<!-- {} -->".format(s)

def main():
    global sHomePath
    global bDebug
    # enable tracebacks of exceptions
    cgitb.enable()

    # check for http args
    form = cgi.FieldStorage()
    # sQuery = form.getvalue("query")
    # if sQuery is None:
    #     sQuery = "n=96"
    # sRoom = form.getvalue("room")
    # if sRoom is None:
    #     sRoom = "media"

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
        
        # handle room queries
        sRooms = ""
        lRooms = {"media": form.getvalue("media"),
                  "garage": form.getvalue("garage")}
        for room in lRooms:
            dprint("lRooms[{}]={}".format(room, lRooms[room]))
            if lRooms[room] is "on":
                sRooms += room + ","
                dprint("room({}) enabled".format(room))
        if len(sRooms) > 0:
            sRooms = sRooms[:-1]
        else:
            sRooms = "media"
        dprint("sRooms={}".format(sRooms))
        
        # handle query type
        queries = {"today": form.getvalue("media"),
                   "24hrs": form.getValue("24hrs"),
                   "12hrs": form.getValue("12hrs"),
                   "6hrs": form.getValue("6hrs")}
        for query in queries:
            if queries[query] is "on":
                if query == "24hrs":
                    sQuery = "n=96"
                elif query == "12hrs":
                    sQuery = "n=48"
                elif query == "6hrs":
                    sQuery = "n=24"
                elif query == "today":
                    sQuery = "today"

        # pull 24 hours of data
        hdb.retrieveData('{} room={}'.format(sQuery, sRooms), bDebug)
        # convert to a format Google Charts can work with
        chartTable = hdb.formatDataForGoogleCharts()
        if chartTable is not "":
            printChartCode(chartTable, sQuery, sRooms)
        else:
            print "<h2>SQL Query was empty, try a different room or query</h2>"
        
        chartOptions()

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
