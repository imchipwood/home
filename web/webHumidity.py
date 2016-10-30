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


#viewWindowMode: 'explicit', viewWindow:{ max=100, min=0} 
def printChartCode(table):
    # this string contains the web page that will be served
    try:
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
          title: 'Media room Temperature/Humidity recordings for today',
          hAxis: { title: 'Date', titleTextStyle: {color: 'blue'}, showTextEvery: 8,
                   slantedText: true, slantedTextAngle: 45
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
    </body>""" % (table)
    except:
        print "-E- failed to create page_str"
        return

    print page_str






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
        # pull 24 hours of data
        hdb.retrieveData('n=96', bDebug=False)
        # convert to a format Google Charts can work with
        chartTable = hdb.formatDataForGoogleCharts()
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