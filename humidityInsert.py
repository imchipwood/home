#!/usr/bin/python -B
import os
import logging
import argparse
import traceback
import paho.mqtt.client as paho
from time import sleep, time
import datetime

from lib.sensors.sensor_humidity import SensorHumidity


def on_connect(client, userdata, flags, rc):
	logging.info("CONNACK received with code %d." % (rc))
	return


def on_publish(client, userdata, mid):
	logging.info("mid: "+str(mid))
	return


def checkLimits(temperature, humidity):
	if -20 <= temperature <= 150 and 0 <= humidity <= 100:
		return True
	return False


def parseArgs():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"configFile",
		type=str,
		help="Config file for sensor & MQTT info"
	)
	parser.add_argument(
		"-nAvg",
		"-n",
		type=int,
		default=5,
		help="# measurements to average. Optional. Default=5"
	)
	parser.add_argument(
		"-debug",
		"-d",
		action="store_true",
		help="Enable debug messages")
	args = parser.parse_args()
	return args


def printData(i, temperature, humidity):
	logging.info(
		"Temperature[{0}]={1:0.1f}, Humidity[{0}]={2:0.1f}".format(
		i,
		temperature,
		humidity
		)
	)
	return


# read config file
# expected keys:
#   dht_type		- DHT type (11, 22, 2302). See Adafruit library for info
#   dht_pin		 - GPIO pin # for DHT sensor
#   mqtt_client	 - name for the client
#   mqtt_broker	 - IP address of MQTT broker
#   mqtt_port	   - Port to use for MQTT broker
#   mqtt_topic_t	- topic for temperature readings
#   mqtt_topic_h	- topic for humidity readings
#   log			 - path to file to log info to
def readConfig(f):
	logging.debug("Using config file found here:\n{}".format(f))
	config = {}
	with open(f, "r") as inf:
		for line in inf:
			line = line.rstrip().split("=")
			key = line[0]
			val = line[1]
			if key in ["dht_pin", "mqtt_port"]:
				val = int(val)
			config[key] = val
			logging.debug("config: found key {} with val {}".format(key, val))
	return config


def logData(f, data, mqtt_rc, mqtt_mid):
	logging.debug("Logging to file: {}".format(f))
	# construct log line
	st = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
	sLog = "{} - {}: {}, RC: {}, mid: {}\n".format(
		st,
		data.keys()[0],
		data[data.keys()[0]],
		mqtt_rc,
		mqtt_mid
	)
	logging.debug("log data:\n-d- {}".format(sLog))
	# write to file
	fileMode = "a"
	if not os.path.exists(f):
		fileMode = "w"
	with open(f, fileMode) as ouf:
		ouf.write(sLog)
	return


def main():

	parsedArgs = parseArgs()
	iAvg = parsedArgs.nAvg
	sConfigFile = parsedArgs.configFile
	bDebug = parsedArgs.debug

	loggingLevel = logging.INFO
	if bDebug:
		loggingLevel = logging.DEBUG
	logging.getLogger().setLevel(loggingLevel)

	dConfig = readConfig(sConfigFile)

	# connect to MQTT broker
	client = paho.Client(client_id=dConfig["mqtt_client"])
	client.on_connect = on_connect
	client.on_publish = on_publish
	client.connect(host=dConfig["mqtt_broker"], port=dConfig["mqtt_port"], keepalive=10)
	client.loop_start()
	sleep(3)

	logging.debug("mqtt info:")
	logging.debug("mqtt_client_id: {}".format(dConfig["mqtt_client"]))
	logging.debug("mqtt_broker:	   {}".format(dConfig["mqtt_broker"]))
	logging.debug("mqtt_port:      {}".format(dConfig["mqtt_port"]))
	logging.debug("mqtt_topic_t:   {}".format(dConfig["mqtt_topic_t"]))
	logging.debug("mqtt_topic_h:   {}".format(dConfig["mqtt_topic_h"]))
	logging.debug("client: {}".format(client))

	# set up the sensor
	logging.debug("Setting up humidity sensor")
	h = SensorHumidity(sensor_type=dConfig["dht_type"], pin=dConfig["dht_pin"], units="f")
	try:
		logging.debug("Beginning 5 warmup readings")
		for i in xrange(0, 5):
			h.read()
			printData(i, h.getTemperature(), h.getHumidity())

		# take N readings and average them
		logging.debug("Beginning {} readings for averaging".format(iAvg))
		fTemperature = 0.0
		fHumidity = 0.0
		for i in xrange(0, iAvg):
			h.read()
			printData(i, h.getTemperature(), h.getHumidity())
			fTemperature += h.getTemperature()
			fHumidity += h.getHumidity()
		fTemperature /= float(iAvg)
		fHumidity /= float(iAvg)
		logging.debug("Final data:")
		logging.debug("Temperature: {0:0.1f}".format(fTemperature))
		logging.debug("Humidity:    {0:0.1f}".format(fHumidity))

		# Send data to server
		if checkLimits(fTemperature, fHumidity):
			try:
				(rc, mid) = client.publish(
					dConfig["mqtt_topic_t"],
					"{0:0.1f}".format(fTemperature),
					qos=2,
					retain=True
				)
				dataDict = {"temperature": fTemperature}
				logData(dConfig["log"], dataDict, rc, mid)
				
				(rc, mid) = client.publish(
					dConfig["mqtt_topic_h"],
					"{0:0.1f}".format(fHumidity),
					qos=2,
					retain=True
				)
				dataDict = {"humidity": fHumidity}
				logData(dConfig["log"], dataDict, rc, mid)
			except:
				raise
		
	except KeyboardInterrupt:
		logging.info("KeyboardInterrupt, exiting gracefully")
		pass

	except Exception as e:
		logging.exception("Some exception: {}".format(e))
		traceback.print_exc()
		raise e

	finally:
		logging.debug("cleaning up")
		client.loop_stop()
		client.unsubscribe(dConfig["mqtt_topic_t"])
		client.unsubscribe(dConfig["mqtt_topic_h"])
		client.disconnect()
	return True


if __name__ == "__main__":
	main()
