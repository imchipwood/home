#!/usr/bin/python
# https://www.raspberrypi.org/learning/getting-started-with-picamera/worksheet/
from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.rotation = 180
camera.brightness = 50
camera.contrast = 50
camera.start_preview()
sleep(5)
camera.capture('/home/cpw/camera/captures/garage.jpg')

# command to open video: omxplayer video.h264
#camera.start_recording('/home/cpw/camera/recordings/video.h264')
#sleep(10)
#camera.stop_recording(
camera.stop_preview()
