import subprocess
import argparse

global DEBUG


def parse_args():
	"""
	Set up an argument parser and return the parsed arguments
	@return: Result of calling parse_args() on the argparse.ArgumentParser object
	@rtype: argparse.Namespace
	"""
	description = "Simple script to check connectivity and attempt to " \
		"recover in case no connection is made"
	parser = argparse.ArgumentParser(description=description)
	parser.add_argument(
		"--address",
		"-a",
		default="192.168.1.1",
		type=str,
		help="Address to ping for connection test"
	)
	parser.add_argument(
		"--interface",
		"-i",
		default="wlan0",
		type=str,
		help="LAN interface to restart as first attempt at recovering"
	)
	parser.add_argument(
		"--noreboot",
		"-nr",
		default=True,
		action="store_true",
		help="Flag to disable rebooting the Pi if no connection"
	)
	parser.add_argument(
		"--debug",
		"-d",
		action="store_true",
		help="Debug mode - execute but don't actually do anything"
	)
	return parser.parse_args()


def WLAN_check(ping_address, interface, noreboot=False):
	"""
	This function checks if the WLAN is still up by pinging the target address
	@param ping_address: target address to ping
	@type ping_address: str
	@param interface: target LAN interface
	@type interface: str
	@param noreboot: Flag to disable rebooting. Default: False (allow reboot)
	@type noreboot: bool
	"""
	flag = True
	for i in range(2 if not noreboot else 1):
		flag = check_connection(ping_address, interface, flag)
		msg = "Connection attempt {} - ".format(i + 1)
		if flag:
			# Connection is good - exit
			msg += "Success! Exiting..."
			print(msg)
			return
		else:
			msg += "Failed! "
			msg += "Rebooting Pi..." if not noreboot else "Exiting..."
			print(msg)


def restart_pi():
	"""
	Restart the Pi as a last ditch effort
	"""
	subprocess.call(
		['logger "WLAN down - Pi forcing reboot"'],
		shell=True
	)
	subprocess.call(['sudo reboot'], shell=True)


def restart_interface(interface):
	"""
	Restart the specified LAN interface
	@param interface: target LAN interface
	@type interface: str
	"""
	# try to recover the connection by resetting the LAN
	subprocess.call(
		['logger "WLAN down - Pi resetting WLAN"'],
		shell=True
	)
	cmd = "sudo /sbin/ifdown {iface} && sleep 10 && " \
		"sudo /sbin/ifup --force {iface}".format(iface=interface)
	subprocess.call(
		[cmd],
		shell=True
	)


def check_connection(ping_address, interface, restart_interface_flag=True):
	"""
	Ping the address & either reboot the LAN interface
	@param ping_address: address to ping
	@type ping_address: str
	@param interface: target interface to reboot
	@type interface: str
	@param restart_interface_flag: Reboot flag - True: interface, False: Pi
	@type restart_interface_flag: bool
	@return: Result of ping - True if response received, False otherwise
	@rtype: bool
	"""
	# This command pings the target address & looks for "1 received"
	# It will return 0 if the ping is successful, and non-zero if not
	ping_cmd = 'ping -c 2 -w 1 -q {} | grep "1 received" > ' \
		'/dev/null 2> /dev/null'.format(ping_address)
	response = subprocess.call([ping_cmd], shell=True)

	if response != 0:
		# Did not get a response
		if restart_interface_flag:
			# Try to reboot the interface first
			if not DEBUG:
				restart_interface(interface)
			# Set flag to false so next iteration attempts a reboot
			restart_interface_flag = False
		else:
			# Already tried rebooting interface - restart Pi in desperation
			if not DEBUG:
				restart_pi()
	else:
		# Response received - No need to continue
		restart_interface_flag = True

	return restart_interface_flag


if __name__ == "__main__":
	global DEBUG
	args = parse_args()
	DEBUG = args.debug
	print(
		"Address: {}\nInterface: {}\nDo not reboot: {}\nDEBUG: {}".format(
			args.address,
			args.interface,
			args.noreboot,
			DEBUG
		)
	)
	WLAN_check(args.address, args.interface, args.noreboot)
