#!/usr/bin/python
import os
import paramiko
from pushbullet import Pushbullet
import argparse


def parseArgs():
	# argument parsing
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"configFile",
		type=str,
		help="Config file for pushbullet & image location settings"
	)
	parser.add_argument(
		"imagePath",
		type=str,
		help="Path to the image file to send"
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
	debug = parsedArgs.debug
	cfgFile = parsedArgs.configFile
	imagePath = parsedArgs.imagePath

	# get image name
	imageName = os.path.basename(imagePath)

	# check the pushbullet API
	settings = parseConfig(cfgFile)
	pushbullet_api = settings['pushbullet_api']
	if not pushbullet_api:
		raise IOError("Couldn't find pushbullet_api in config file {}".format(cfgFile))

	# check the ssh settings
	expectedSSHSettings = ['ssh_client_ip', 'ssh_client_username', 'ssh_client_password']
	for setting in expectedSSHSettings:
		if setting not in settings.keys():
			raise IOError("{} not found in config file".format(setting))
		elif not settings[setting]:
			raise IOError("{} found but with bad value: {} ".format(setting, settings[setting]))

	# create the SSH and SFTP clients
	ssh_client = paramiko.SSHClient()
	ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh_client.connect(
		settings['ssh_client_ip'],
		username=settings['ssh_client_username'],
		password=settings['ssh_client_password']
	)
	sftp_client = ssh_client.open_sftp()

	# create the pushbullet client
	pb = Pushbullet(pushbullet_api)

	# get the file from the remote machine
	with sftp_client.open(imagePath) as pic:
		file_data = pb.upload_file(pic, imageName)

	# push the file as a notification
	push = pb.push_file(**file_data)

	return


def parseConfig(f):
	with open(f, "r") as inf:
		lines = inf.readlines()

	settings = {}
	for line in lines:
		# skip commented out lines, blank lines, and lines without an = sign
		if line[0] == '#' or line[:2] == '//' or line == '\n' or '=' not in line:
			continue

		line = line.rstrip().split("=")
		print(line)

		key, val = line[:2]
		settings[key] = val

	return settings

if __name__ == "__main__":
	main()
