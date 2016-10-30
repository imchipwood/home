#!/usr/bin/env python

import cgi
import cgitb
import sys
import os
import argparse
import traceback

sys.path.append('/home/pi/dev/home/lib/db')
from db_humidity import DBHumidity

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

def printChartCode(table):
    # this string contains the web page that will be served
    page_str="""
    <body>    
    <h1>Raspberry Pi Humidity/Temperature Logger</h1>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = google.visualization.arrayToDataTable([ ['Date', 'Temperature', 'Humidity'],
%s ]);

        var options = {
          title: 'Google column chart',
          hAxis: {title: 'Date', titleTextStyle: {color: 'blue'}},
          vAxis: {title: 'Count', titleTextStyle: {color: 'blue'}}
        };

        var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
        chart.draw(data, options);
      }
    </script>
    <div id="chart_div" style="width: 900px; height: 500px;"></div>
    </body>""" % table

    print page_str

# convert rows from database into a javascript table
def create_table(lData):
    sChartTable=""

    # build table string for all rows except the final one
    for set in lData[:-1]:
        rowstr="['{0}', {1}, {2}],\n".format(str(set[0]),str(set[1]), str(set[2]))
        sChartTable+=rowstr

    # ensure final row has no extra comma at the end
    finalRow = sChartTable[-1]
    finalRow.replace(',\n','\n')
    sChartTable += finalRow
    
    return sChartTable






def main():
    # enable tracebacks of exceptions
    cgitb.enable()
    
    # user-defined args
    sDBAccessFileName = 'sqlget.txt'

    # set up db
    sDBCredentialsFile = "/home/pi/dev/home/conf/" + sDBAccessFileName
    hdb = DBHumidity(sDBCredentialsFile, bDebug=False)

    printHTTPheader()
    printHTMLhead("Raspberry Pi Humidity/Temperature Tracker")

    # do query and format the data
    try:
        hdb.retrieveData('today', bDebug=False)
        chartData = hdb.formatDataForGoogleCharts()
        chartTable = create_table(chartData)
        printChartCode(chartTable)
    except KeyboardInterrupt:
        print "\n\t-e- KeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\t-E- Some exception: %s\n" % (e)
        traceback.print_exc()
        raise e

    print "</html>"
    return

if __name__=="__main__":
    main()