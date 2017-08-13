#!/usr/bin/python
# https://www.raspberrypi.org/learning/getting-started-with-picamera/worksheet/
import os
# from time import sleep
from picamera import PiCamera

camera = PiCamera()
camera.rotation = 180
camera.brightness = 50
camera.contrast = 50
# camera.start_preview()
# sleep(5)

# make sure the dirs to save the image to actually exist
jpgDir = '/home/cpw/camera/captures/'
if not os.path.exists(jpgDir):
	os.makedirs(jpgDir)

# image path - try to delete it in case we can't overwrite it for whatever reason
jpgPath = os.path.join(jpgDir, 'cameraTest.jpg')
if os.path.exists(jpgPath):
	try:
		os.remove(jpgPath)
	except:
		print("failed to remove test camera file, hopefully it just gets overwritten...")
		pass

# capture the image
camera.capture(jpgPath)

# command to open video: omxplayer video.h264
#camera.start_recording('/home/cpw/camera/recordings/video.h264')
#sleep(10)
#camera.stop_recording(
# camera.stop_preview()
