#!/usr/bin/python
from picamera import PiCamera
from time import sleep

camera = PiCamera()
#camera.rotation = 180
camera.start_preview()
sleep(5)
camera.capture('/home/cpw/camera/captures/test000.jpg')
camera.stop_preview()
