#!/usr/bin/python
import logging
import argparse
import traceback
from time import sleep
from library.sensors.doorController import DoorController

_description = "door.py - A Raspberry Pi-based door monitor with PiCamera & PushBullet notification support."


def parseArgs():
	"""

	@return:
	@rtype:
	"""
	parser = argparse.ArgumentParser(description=_description)
	parser.add_argument(
		"doorConfigFile",
		type=str,
		help="Config file for door monitoring/control - required"
	)
	parser.add_argument(
		"-c",
		"--cameraConfigFile",
		type=str,
		help="Config file for camera control - optional"
	)
	parser.add_argument(
		"-p",
		"--pushbulletConfigFile",
		type=str,
		help="Config file for PushBullet notifications - optional"
	)
	parser.add_argument(
		'-d',
		'--debug',
		action="store_true",
		help="Enable debug messages - optional"
	)

	args = parser.parse_args()
	return args


def main():
	# Parse the arguments and create the door controller
	parsedArgs = parseArgs()

	door = DoorController(
		doorConfigFile=parsedArgs.doorConfigFile,
		cameraConfigFile=parsedArgs.cameraConfigFile,
		pushbulletConfigFile=parsedArgs.pushbulletConfigFile,
		debug=parsedArgs.debug
	)

	# Launch the door control thread & wait for something bad to happen
	try:
		door.start()
		while True:
			sleep(10)

	except KeyboardInterrupt:
		logging.info("gd: KeyboardInterrupt, exiting gracefully")

	except Exception as e:
		logging.exception("gd: Some exception:\n{}\n".format(e))
		# traceback.print_exc()
		raise e

	finally:
		# Gracefully shut everything down
		door.cleanup()


if __name__ == '__main__':
	main()
