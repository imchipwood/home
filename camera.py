#!/usr/bin/python
import logging
import argparse
from lib.sensors.mqttCamera import MqttCamera
from time import sleep
import traceback


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


def main():
	parsedArgs = parseArgs()
	cfgFile = parsedArgs.configFile
	bDebug = parsedArgs.debug

	camera = MqttCamera(configFile=cfgFile, debug=bDebug)

	try:
		camera.start()
		while True:
			sleep(10)

	except KeyboardInterrupt:
		logging.info("-i- gd: KeyboardInterrupt, exiting gracefully")
		raise

	except Exception as e:
		logging.exception("-E- gd: Some exception: {}\n".format(e))
		traceback.print_exc()
		raise e

	finally:
		camera.cleanup()

	return

if __name__ == '__main__':
	main()
