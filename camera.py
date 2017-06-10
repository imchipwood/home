#!/usr/bin/python
import logging
from time import sleep
import paho.mqtt.client as paho
from picamera import PiCamera


def on_connect(client, userdata, flags, rc):
	print("CONNACK received with code %d." % (rc))


def on_subscribe(client, userdata, mid, granted_qos):
	print("Subscribed: "+str(mid)+" "+str(granted_qos))


def on_message(client, userdata, msg):
	print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))


def parseArgs():
	# argument parsing
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"configFile",
		type=str,
		help="Config file for camera settings & MQTT host/topic info"
	)
	parser.add_argument(
		'-debug',
		'-d',
		action="store_true",
		help="Enable debug messages - optional"
	)

	args = parser.parse_args()
	return args


def parseConfig(cfgFile):
	cameraSettings = {}
	mqttSettings = {}

	with open(cfgFile, 'r') as inf:
		lines = inf.readlines()

	for line in lines:
		line = line.rstrip().split("=")
		key, val = line[:2]
		if 'camera' in key:
			cameraSettings[key] = val
		elif 'mqtt' in key:
			mqttSettings[key] = val

	return cameraSettings, mqttSettings

#
# camera = PiCamera()
# camera.rotation = 180
# camera.brightness = 50
# camera.contrast = 50
# camera.start_preview()
# sleep(5)
# camera.capture('/home/cpw/camera/captures/garage.jpg')

def main():
	parsedArgs = parseArgs()
	cfgFile = parsedArgs.cfgFile
	debug = parsedArgs.debug

	loggingLevel = logging.INFO
	if bDebug:
		loggingLevel = logging.DEBUG
	logging.getLogger().setLevel(loggingLevel)

	cameraSettings, mqttSettings = parseConfig(cfgFile=cfgFile)
	logging.debug(cameraSettings)
	logging.debug(mqttSettings)
	return

if __name__ == '__main__':
	main()