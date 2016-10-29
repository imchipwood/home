#!/usr/bin/python
#from sensor_humidity import Humidity
import sys
import time
sys.path.append('/home/pi/dev/home/lib/sensors')
from sensor_humidity import SensorHumidity

def main():
    # test fake sensor type
    try:
        print "----------\nTest 1 - fake sensor_type"
        test1 = SensorHumidity(sensor_type='fake', pin=4, units='f')
    except Exception as e:
        print "caught fake sensor_type exception"
        print "{}\n".format(e)
        pass
    # test fake units
    try:
        print "----------\nTest 2 - fake units"
        test2 = SensorHumidity(sensor_type='22', pin=4, units='fake')
    except Exception as e:
        print "caught fake units exception"
        print "{}\n".format(e)
        pass
    # test non-string sensor type
    try:
        print "----------\nTest 3 - sensor_type as integer"
        test3 = SensorHumidity(sensor_type=22, pin=4, units='f')
        print "Successfully set sensor type using an integer\n"
    except Exception as e:
        print "Setting non-string sensor type failed"
        print "{}\n".format(e)
        pass

    print "----------\nTest 4 - sensor_type as string"
    h = SensorHumidity(sensor_type='22', pin=4, units='f')
    print "Successfully set sensor type using a string\n"

    try:
        i = 0
        while (i < 2):
            i += 1
            h.read()
            localtime = time.asctime( time.localtime(time.time()) )
            print "{3} : Temp={0:0.1f}*{1}, Humidity={2:0.1f}%".format(h.getTemperature(), h.getUnits().upper(), h.getHumidity(), localtime)
            time.sleep(2)
    except KeyboardInterrupt:
        print "\n\tKeyboardInterrupt, exiting gracefully\n"
        sys.exit(1)
    except Exception as e:
        print "\n\tSome exception: %s\n" % (e)
        raise e

    print "\n----------\nTests completed. Humidity sensor library functioning properly"
    return True

if __name__ == '__main__':
    main()
