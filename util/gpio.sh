#! /bin/bash
#echo "14" > /sys/class/gpio/export
#echo "low" > /sys/class/gpio/gpio14/direction
#echo "14" > /sys/class/gpio/unexport

# Initializes all gpio pins to output mode and sets them all LOW
#sleep 1
for i in `seq 0 16`; do /usr/local/bin/gpio mode $i out; done
for i in `seq 0 16`; do /usr/local/bin/gpio write $i 0; done