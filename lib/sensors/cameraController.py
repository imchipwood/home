import logging
import traceback
import ephem
from time import sleep
from picamera import PiCamera


class PiCameraController(PiCamera):
	def __init__(self, configFile, debug=False):
		PiCamera.__init__(self)

		# handle logging level
		self.logger = logging.getLogger(__name__)
		loggingLevel = logging.INFO
		if debug:
			loggingLevel = logging.DEBUG

		# logging level has to be set globally for some reason
		logging.getLogger().setLevel(loggingLevel)

		# read the config file
		self.cameraSettings = self.parseConfig(cfgFile=configFile)

		# finish setting up logging
		self.setupLogging(loggingLevel=debug, logFile=self.cameraSettings['log'])

		# configure the camera
		self.cameraFile = None
		self.cameraDelay = None
		self.cameraSetup(self.cameraSettings)
		return

	def parseConfig(self, cfgFile):
		cameraSettings = {}
		logFile = None

		with open(cfgFile, 'r') as inf:
			lines = inf.readlines()

		for line in lines:
			# skip commented out lines, blank lines, and lines without an = sign
			if line[0] == '#' or line[:2] == '//' or line == '\n' or '=' not in line:
				continue

			# line is good, split it by '=' to get token and value
			line = line.rstrip().split("=")
			key, val = line[:2]

			# try to convert the value to an int. some values will be strings so this won't work, but
			# it means we don't have to do the conversions elsewhere
			try:
				val = int(val)
			except:
				pass

			if 'camera' in key:
				key = "_".join(key.split('_')[1:])
				cameraSettings[key] = val

		return cameraSettings

	def setupLogging(self, loggingLevel, logFile=None):

		if loggingLevel == logging.DEBUG:
			val = 'DEBUG'
		else:
			val = 'INFO'
		logging.info("Logging level: {}".format(val))

		# stdout stream handler
		ch = logging.StreamHandler()
		ch.setLevel(loggingLevel)

		# stdout logging formatting
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)
		ch.setFormatter(stdoutFormatter)
		self.logger.addHandler(ch)

		# set up file handler logger
		if logFile:
			fh = logging.FileHandler(logFile)
			fh.setLevel(logging.DEBUG)

			# file logging formatting
			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fh.setFormatter(fileFormatter)
			self.logger.addHandler(fh)
		return

	def cameraSetup(self, settings):
		"""Set up the PiCamera based on settings found in config file

		@return: None
		"""
		self.logger.debug("cameraSetup")
		self.logger.debug(settings)
		# self.camera = PiCamera()
		cameraSettingsKeys = settings.keys()

		if 'rotation' in cameraSettingsKeys:
			self.rotation = settings['rotation']

		if 'brightness' in cameraSettingsKeys:
			self.brightness = settings['brightness']

		if 'contrast' in cameraSettingsKeys:
			self.contrast = settings['contrast']

		if 'resolution' in cameraSettingsKeys:
			width, height = [int(x) for x in settings['resolution'].split(',')]
			self.logger.debug("setting camera resolution to width, height: {}, {}".format(width, height))
			self.resolution = (width, height)

		if 'filepath' in cameraSettingsKeys:
			self.cameraFile = settings['filepath']
		else:
			raise IOError("No specified filepath for camera found in config file")

		if 'delay' in cameraSettingsKeys:
			self.cameraDelay = settings['delay']

		# set the ISO based on whether or not the sun is up
		self.updateCameraISO()

		# self.start_preview()
		return

	def updateCameraISO(self, iso=None):
		"""Update the camera ISO. Supports daytime/nighttime ISO values set up in the cameraSettings dict,
		directly specifying the ISO as a function argument, or an ISO key in the cameraSettingsDict.

		@remark: function arg takes preference, then city/daytime/nighttime values in cameraSettings dict, then 'iso' key
		 in cameraSettings dict

		@param iso: Optional, integer, ISO to set the camera to
		@return:
		"""
		if iso:
			self.iso = iso
		elif 'city' in self.cameraSettings.keys():
			sun = ephem.Sun()
			sea = ephem.city(self.cameraSettings['city'])
			sun.compute(sea)
			twilight = -12 * ephem.degree
			isDaytime = sun.alt < twilight

			if 'iso_daytime' in self.cameraSettings.keys():
				daytimeISO = self.cameraSettings['iso_daytime']
			else:
				daytimeISO = 200

			if 'iso_nighttime' in self.cameraSettings.keys():
				nighttimeISO = self.cameraSettings['iso_nighttime']
			else:
				nighttimeISO = 800

			iso = daytimeISO
			if not isDaytime:
				iso = nighttimeISO

			self.logger.debug("setting camera ISO to {}".format(iso))
			self.iso = iso
		elif 'iso' in self.cameraSettings.keys():
			self.iso = self.cameraSettings['iso']
		else:
			self.logger.info("no 'city' or 'iso' found in config file, leaving ISO as default")
		return

	def cleanup(self):
		"""Attempt to gracefully exit the program

		@return: None
		"""
		self.logger.info("cleaning up")

		try:
			self.logger.debug("disabling camera")
			self.stop_preview()
			self.logger.debug("camera disabled")
		except Exception as e:
			self.logger.exception("Exception while shutting down camera: {}".format(e))
			traceback.print_exc()
			pass

		return

	def capture(self, output=None, format=None, use_video_port=False, resize=None, splitter_port=0, delay=None, **options):
		"""slight modification on built-in capture function to allow not specifying an output and updating camera ISO
		on the fly based on time of day

		@remark: More info here: http://picamera.readthedocs.io/en/release-1.10/api_camera.html

		@param output: Optional, string path to save image to. Defaults to cameraFile attribute if none provided
		@param format: Optional, format to save image in (jpeg, png, gif, etc.)
		@param use_video_port: Optional, boolean, defaults False. Set to true to use video port instead of camera port if you need rapid capture
		@param resize: Optional, tuple of (width, height) to resize image. defaults to None (no resize)
		@param splitter_port: Optional, boolean, default 0, ignored when use_video_port=False. Defines port of video splitter that image encoder will be attached to
		@param delay: Optional, integer, default None, use to delay the camera picture taking by 'delay' seconds
		@param options: no documentation provided by picamera docs
		@return: None
		"""
		if not output:
			output = self.cameraFile
		self.updateCameraISO()
		if delay:
			self.logger.debug("delaying {} seconds before taking photo".format(delay))
			sleep(delay)
		elif self.cameraDelay:
			self.logger.debug("delaying {} seconds before taking photo".format(self.cameraDelay))
			sleep(self.cameraDelay)
			
		super(PiCameraController, self).capture(
			output=output,
			format=format,
			use_video_port=use_video_port,
			resize=resize,
			splitter_port=splitter_port,
			**options
		)
		return
