#!/usr/bin/python -B
import os
import logging
import argparse
import traceback
import paho.mqtt.client as paho
from time import sleep, time
import datetime

from library.sensors.sensor_humidity import SensorHumidity
from library.config.environmentConfig import EnvironmentConfig


def on_connect(client, userdata, flags, rc):
	logging.info("CONNACK received with code %d." % (rc))


def on_publish(client, userdata, mid):
	logging.info("mid: "+str(mid))


def checkLimits(temperature, humidity):
	tempLowLimit = -2
	tempHighLimit = 150
	tempGood = False
	if tempLowLimit <= temperature <= tempHighLimit:
		tempGood = True
	else:
		logging.info(
			"Temperature outside of limits (low:{}, high:{})".format(
				tempLowLimit, tempHighLimit
			)
		)

	humidLowLimit = 0
	humidHighLimit = 100
	humidGood = False
	if humidLowLimit <= humidity <= humidHighLimit:
		humidGood = True
	else:
		logging.info(
			"Humidity outside of limits (low:{}, high:{})".format(
				humidLowLimit, humidHighLimit
			)
		)

	return tempGood & humidGood


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


def logData(f, data, mqtt_rc, mqtt_mid):
	logging.debug("Logging to file: {}".format(f))

	# construct log line
	st = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')

	# dict
	dataStr = ""
	for key, value in data.items():
		dataStr += "{}: {:06.2f}, ".format(key, value)
	dataStr = dataStr[:-2]

	if mqtt_rc or mqtt_mid:
		sLog = "{} - RC: {}, mid: {}, {}\n".format(
			st,
			mqtt_rc,
			mqtt_mid,
			dataStr
		)
	else:
		sLog = "{} - {}\n".format(
			st,
			dataStr
		)
	logging.debug("log data:\n-d- {}".format(sLog))
	# write to file
	fileMode = "a"
	if not os.path.exists(f):
		fileMode = "w"
	with open(f, fileMode) as ouf:
		ouf.write(sLog)


def main():

	parsedArgs = parseArgs()
	readingsToAverage = parsedArgs.nAvg
	configFilePath = parsedArgs.configFile
	debugEnable = parsedArgs.debug

	loggingLevel = logging.INFO
	if debugEnable:
		loggingLevel = logging.DEBUG
	logging.getLogger().setLevel(loggingLevel)

	config = EnvironmentConfig(configFilePath)
	mqttSettings = config.mqtt

	client = paho.Client(client_id=mqttSettings.client)

	logging.debug("mqtt info:")
	logging.debug("mqtt_client_id: {}".format(mqttSettings.client))
	logging.debug("mqtt_broker:	   {}".format(mqttSettings.broker))
	logging.debug("mqtt_port:      {}".format(mqttSettings.port))
	logging.debug("mqtt_topic_t:   {}".format(mqttSettings.topicTemperature))
	logging.debug("mqtt_topic_h:   {}".format(mqttSettings.topicHumidity))
	logging.debug("client: {}".format(client))

	# set up the sensor
	logging.debug("Setting up humidity sensor")
	environmentSensor = SensorHumidity(sensorType=config.dhtType, pin=config.dhtPin, units="fahrenheit")
	try:
		logging.debug("Beginning 5 warmup readings")
		for i in xrange(0, 5):
			environmentSensor.read()
			printData(i, environmentSensor.temperature, environmentSensor.humidity)

		# take N readings and average them
		logging.debug("Beginning {} readings for averaging".format(readingsToAverage))
		cumulativeTemperature = 0.0
		cumulativeHumidity = 0.0
		for i in xrange(0, readingsToAverage):
			environmentSensor.read()
			printData(i, environmentSensor.temperature, environmentSensor.humidity)
			cumulativeTemperature += environmentSensor.temperature
			cumulativeHumidity += environmentSensor.humidity
		averageTemperature = cumulativeTemperature / float(readingsToAverage)
		averageHumidity = cumulativeHumidity / float(readingsToAverage)
		logging.debug("Final data:")
		logging.debug("Temperature: {0:0.1f}".format(averageTemperature))
		logging.debug("Humidity:    {0:0.1f}".format(averageHumidity))
		dataDict = {"temperature": averageTemperature, "humidity": averageHumidity}
		logData(config.log, dataDict, None, None)

		# Send data to server
		if checkLimits(averageTemperature, averageHumidity):
			try:
				# connect to MQTT broker
				logging.debug("Connecting to MQTT broker")
				client.on_connect = on_connect
				client.on_publish = on_publish
				client.connect(host=mqttSettings.broker, port=mqttSettings.port, keepalive=10)
				client.loop_start()
				sleep(3)

				(rc, mid) = client.publish(
					mqttSettings.topicTemperature,
					"{0:0.1f}".format(averageTemperature),
					qos=2,
					retain=True
				)
				dataDict = {"temperature": averageTemperature}
				logData(config.log, dataDict, rc, mid)
				
				(rc, mid) = client.publish(
					mqttSettings.topicHumidity,
					"{0:0.1f}".format(averageHumidity),
					qos=2,
					retain=True
				)
				dataDict = {"humidity": averageHumidity}
				logData(config.log, dataDict, rc, mid)
			except:
				logging.debug("some MQTT failure. Ignoring")
				pass
		else:
			logging.warning("Temperature failed limit check")
		
	except KeyboardInterrupt:
		logging.info("KeyboardInterrupt, exiting gracefully")
		pass

	except Exception as e:
		logging.exception("Some exception: {}".format(e))
		traceback.print_exc()
		raise e

	finally:
		logging.debug("cleaning up")
		try:
			client.loop_stop()
			client.unsubscribe(mqttSettings.topicTemperature)
			client.unsubscribe(mqttSettings.topicHumidity)
			client.disconnect()
		except:
			pass


if __name__ == "__main__":
	main()
