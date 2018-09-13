import os
import re

from definitions import LOG_DIR

LOG_FILE_NAME = 'garage.txt'
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)


def main():

	with open(LOG_FILE_PATH, 'r') as inf:
		lines = inf.readlines()
		lines.reverse()

	# example lines we're looking for:
	# 2017-10-02 08:50:10,581 - library.sensors.doorController - DEBUG - monitor state: 0
	# 2017-10-02 08:54:18,600 - library.sensors.doorController - DEBUG - monitor state: 1
	# 2017-10-02 08:56:00,410 - library.sensors.doorController - DEBUG - monitor state: 0
	# regex for that:
	reg = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+\s*-\s*library\.sensors\.doorController\s*-\s*\w+\s*-\s*monitor state:\s*(\d+)')

	for line in lines:
		matcher = reg.match(line)
		if matcher:
			timestamp = matcher.group(1)
			state = "OPEN" if matcher.group(2) == '1' else "CLOSED"
			print("Door {} @ {}".format(state, timestamp))
			return


if __name__ == "__main__":
	main()
