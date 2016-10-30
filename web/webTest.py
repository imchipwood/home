#!/usr/bin/env python

import cgi
import cgitb


# print data from a file formatted as a javascript array
# return a string containing the table
#
def print_table(filename,delimiter):
    data_lines=[]
    result=""
    with open(filename) as data_file:
        data_lines=data_file.readlines()
        for line in data_lines[:-1]:
            x, y=line.strip('\n').split(delimiter)
            result += "['"+x+"', "+y+"],\n"
        else:
            x, y=data_lines[-1].strip('\n').split(delimiter)
            result += "['"+x+"', "+y+"]"

    return result

# print an HTTP header
#
def printHTTPheader():
    print "Content-type: text/html"
    print ""
    print ""

def printHTMLhead(sTitle, lTable):
    print "<html>"
    print "    <head>"
    print "        <title>{}</title>".format(sTitle)
    printGraphTable(lTable)
    print "    </head>"

def printChartCode(table):

    # this string contains the web page that will be served
    page_str="""
    <body>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = google.visualization.arrayToDataTable([ ['Date', 'Count'], %s ]);

        var options = {
          title: 'Google column chart',
          hAxis: {title: 'Date', titleTextStyle: {color: 'blue'}},
          vAxis: {title: 'Count', titleTextStyle: {color: 'blue'}}
        };

        var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
        chart.draw(data, options);
      }
    </script>
    <div id="chart_div"></div>
    </body>""" % table

    # serve the page with the data table embedded in it
    print page_str
    print '<div id="chart_div" style="width: 900px; height: 500px;"></div>'

def main():
    # enable tracebacks of exceptions
    cgitb.enable()

    printHTTPheader()
    printHTMLhead("Raspberry Pi Humidity/Temperature Tracker")
    printChartCode(lDataTable)
    print "</html>"
    
    return

if __name__=="__main__":
    main()