#!/usr/bin/env python

import cgi
import cgitb

# enable tracebacks of exceptions
cgitb.enable()

# print an HTTP header
def printHTTPheader():
    print "Content-type: text/html"
    print ""
    print ""

def main():

    printHTTPheader()

    # webpage data
    page_str="""
        <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
        <script type="text/javascript">
          google.charts.load('current', {'packages':['scatter']});
          google.charts.setOnLoadCallback(drawChart);
    
          function drawChart () {
    
            var data = new google.visualization.DataTable();
            data.addColumn('string', 'Date & Time');
            data.addColumn('number', 'Temperature');
            data.addColumn('number', 'Humidity');
    
            data.addRows([%s]);
    
            var options = {
              chart: {
                title: 'Temperature & Humidity over time',
                subtitle: ''
              },
              width: 800,
              height: 500,
              series: {
                0: {axis: 'temperature'},
                1: {axis: 'humidity'}
              },
              axes: {
                y: {
                  'temperature': {label: 'Temperature (F)'},
                  'humidity': {label: '% Humidity'}
                }
              }
            };
    
            var chart = new google.charts.Scatter(document.getElementById('scatter_dual_y'));
    
            chart.draw(data, options);
    
          }
        </script>
    """ % hdb.formatDataForGoogleCharts()

    # serve the page with the data table embedded in it
    print page_str

if __name__=="__main__":
    main()
