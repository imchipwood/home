#!/usr/bin/python
import logging
import argparse
import traceback
from time import sleep
from lib.sensors.doorController import DoorController


def parseArgs():
	# argument parsing
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"configFile",
		type=str,
		help="Config file for DoorController - required"
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
	sGarageDoorFilePath = parsedArgs.configFile
	bDebug = parsedArgs.debug

	try:
		door = DoorController(sGarageDoorFilePath, bDebug)
	except:
		raise

	try:
		door.start()
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
		door.cleanup()

	return


if __name__ == '__main__':
	main()
