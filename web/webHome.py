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


def printGarageDoor(form, ddb):
    # get garage door status
    ddb.retrieveData("n=1 room=garage", bDebug)
    state = ddb.getDataRaw()[-1][-1]
    sGarageState = "    <h1>Garage door is: "
    if state == 0:
        sGarageState += '<span style="color:green">Closed</span>'
    elif 0 < state < 100:
        sGarageState += '<span style="color:yellow">Moving</span>'
    elif state == 100:
        sGarageState += '<span style="color:red">Open</span>'
    sGarageState += "</h1>"
    print sGarageState
    # make a refresh button
    print ('    <form><input type="button" '
        'onClick="history.go(0)" '
        'value="Refresh"></form>')


def generateHumidityQuery(form):
    sRooms = ""
    lRooms = {"media": form.getvalue("media"),
              "garage": form.getvalue("garage")}
    for room in lRooms:
        # dprint("lRooms[{}]={}".format(room, lRooms[room]))
        if lRooms[room] == "on":
            sRooms += room + ","
    if len(sRooms) > 0:
        sRooms = sRooms[:-1]
    else:
        sRooms = "media"
    # handle query type
    sQuery = "n=96"
    queries = {"today": "today",
               "24hrs": "n=96",
               "12hrs": "n=48",
               "6hrs": "n=24"}
    fQuery = form.getvalue("query")
    if fQuery is not None:
        sQuery = queries[fQuery]
    return (sQuery, sRooms)


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
            var data = google.visualization.arrayToDataTable([ %s, %s ]);
    
            var options = {
                title: 'Temperature/Humidity measurements for query="%s", room="%s"',
                hAxis: {
                    title: 'Date',
                    titleTextStyle: {color: 'blue'},
                    showTextEvery: 8,
                    slantedText: true,
                    slantedTextAngle: 45
                },
                vAxes: {
                    0: {
                        title: 'Temperature in F',
                        titleTextStyle: {color: 'red'}
                    },
                    1: {
                        title: '%% Humidity',
                        titleTextStyle: {color: 'blue'},
                        format:"#%%"
                    }
                },
                colors: ['red', 'blue'],
                series: {
                    0: {targetAxisIndex: 0},
                    1: {targetAxisIndex: 1}
                }
            };
    
            var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
            chart.draw(data, options);
        }
    </script>
    <div id="chart_div" style="width: 900px; height: 500px;"></div>""" % (columnHeaders,
                                                                        table,
                                                                        sQuery,
                                                                        sRooms)
    except:
        print "-E- failed to create page_str"
        return

    print page_str


def chartOptions():
    # room choices
    print ""
    print '<form action="/cgi-bin/webHome.py" method="post" target="_blank">'
    print "    <h4>Room</h4>"
    print '        <input type="checkbox" name="media" value="on" />media<br>'
    print '        <input type="checkbox" name="garage" value="on" />garage'
    print "    <hr>"
    print "    <h4>Query type</h4>"
    print '        <input type="radio" name="query" value="today" />today<br>'
    print '        <input type="radio" name="query" value="24hrs" />last 24 hours<br>'
    print '        <input type="radio" name="query" value="12hrs" />last 12 hours<br>'
    print '        <input type="radio" name="query" value="6hrs" />last 6 hours<br>'
    print '        <input type="submit" value="Execute Query" />'
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
        printGarageDoor(form, ddb)

        # handle room queries
        (sQuery, sRooms) = generateHumidityQuery(form)
        # pull data based on query type, then display
        hdb.retrieveData('{} room={}'.format(sQuery, sRooms), bDebug)
        chartTable = hdb.formatDataForGoogleCharts()
        if chartTable is not "":
            printChartCode(chartTable, sQuery, sRooms)
        else:
            print "<h2>SQL Query was empty, try a different query</h2>"
        # give some options for new queries
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
