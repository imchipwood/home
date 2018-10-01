#!/usr/bin/python
import logging
import argparse
import traceback
from time import sleep
from library.sensors.doorController import DoorController


def parseArgs():
	# argument parsing
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"doorConfigFile",
		type=str,
		help="Config file for door monitoring/control - required"
	)
	parser.add_argument(
		"-cameraConfigFile",
		"-c",
		type=str,
		help="Config file for camera control - optional"
	)
	parser.add_argument(
		"-pushbulletConfigFile",
		"-p",
		type=str,
		help="Config file for PushBullet notifications - optional"
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
	doorConfigFile = parsedArgs.doorConfigFile
	cameraConfigFile = parsedArgs.cameraConfigFile
	pushbulletConfigFile = parsedArgs.pushbulletConfigFile
	debug = parsedArgs.debug

	try:
		door = DoorController(
			doorConfigFile,
			cameraConfigFile,
			pushbulletConfigFile,
			debug=debug
		)
	except:
		raise

	try:
		door.start()
		while True:
			sleep(10)

	except KeyboardInterrupt:
		logging.info("gd: KeyboardInterrupt, exiting gracefully")
		raise

	except Exception as e:
		logging.exception("gd: Some exception: {}\n".format(e))
		traceback.print_exc()
		raise e

	finally:
		door.cleanup()


if __name__ == '__main__':
	main()
