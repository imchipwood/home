import logging
import traceback
import time
import os

try:
	from picamera import PiCamera
except:
	logging.warning("Failed to import picamera - using mock")
	from library.mock.mock_picamera import PiCamera

from library.config.cameraConfig import CameraConfig


class PiCameraController(PiCamera):
	def __init__(self, configFile, debug=False):
		"""
		Constructor for the modified PiCamera used in this project
		Additions:
		- ISO is calculated based on the time of day
		- Logging
		@param configFile: path to configuration file
		@type configFile: str
		@param debug: debug logging flag
		@type debug: bool
		"""
		super(PiCameraController, self).__init__()

		# initalize logger
		self.logger = logging.getLogger(__name__)

		# logging level has to be set globally for some reason
		logging.getLogger().setLevel(logging.DEBUG)

		# read the config file
		self.settings = CameraConfig(configFile)

		# finish setting up logging
		self.setupLogging(loggingLevel=debug, logFile=self.settings.log)

		# configure the camera
		self.cameraFile = None
		self.cameraDelay = None
		self.cameraSetup()
		self.logCurrentSetup()

	def setupLogging(self, loggingLevel=False, logFile=None):
		"""
		Set up logging stream and file handlers
		@param loggingLevel: logging level as defined by logging package
		@type loggingLevel: int
		@param logFile: (optional) path for file logging
		@type logFile: str
		"""
		if loggingLevel:
			val = 'DEBUG'
		else:
			val = 'INFO'
		self.logger.info("Logging level: {}".format(val))

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
			self.logger.info("Logging to file: {}".format(logFile))
			fh = logging.FileHandler(logFile)
			fh.setLevel(logging.DEBUG)

			# file logging formatting
			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fh.setFormatter(fileFormatter)
			self.logger.addHandler(fh)

	def logCurrentSetup(self):
		"""
		Log the current setup to file
		"""
		self.logger.debug("\n----------------------------------------")
		self.logger.debug("\nCamera Settings:\n{}".format(self.settings))

	def cameraSetup(self):
		"""
		Set up the PiCamera based on settings found in config file
		"""
		self.logger.debug("cameraSetup")
		self.rotation = self.settings.rotation
		self.brightness = self.settings.brightness
		self.contrast = self.settings.contrast
		self.resolution = self.settings.resolution
		self.cameraFile = self.settings.capturePath
		self.cameraDelay = self.settings.captureDelay
		self.iso = self.settings.iso

	def cleanup(self):
		"""
		Attempt to gracefully exit the program
		"""
		self.logger.info("cleaning up")

		try:
			self.logger.debug("disabling camera")
			self.stop_preview()
			self.close()
			self.logger.debug("camera disabled")
		except Exception as e:
			self.logger.exception("Exception while shutting down camera: {}".format(e))
			traceback.print_exc()
			pass

	def capture(self, output=None, format=None, use_video_port=False, resize=None, splitter_port=0, delay=None, **options):
		"""
		slight modification on built-in capture function to allow not specifying an output and updating camera ISO
		on the fly based on time of day

		@remark: More info here: http://picamera.readthedocs.io/en/release-1.10/api_camera.html

		@param output: Optional, string path to save image to. Defaults to cameraFile attribute if none provided
		@param format: Optional, format to save image in (jpeg, png, gif, etc.)
		@param use_video_port: Optional, boolean, defaults False. Set to true to use video port instead of camera port if you need rapid capture
		@param resize: Optional, tuple of (width, height) to resize image. defaults to None (no resize)
		@param splitter_port: Optional, boolean, default 0, ignored when use_video_port=False. Defines port of video splitter that image encoder will be attached to
		@param delay: Optional, integer, default None, use to delay the camera picture taking by 'delay' seconds
		@param options: no documentation provided by picamera docs
		"""
		if not output:
			output = self.settings.capturePath

		if os.path.exists(output):
			os.remove(output)

		# update iso
		self.iso = self.settings.iso

		# Do any delay
		if delay:
			self.logger.debug("delaying {} seconds before taking picture".format(delay))
			time.sleep(delay)
		elif self.cameraDelay:
			self.logger.debug("delaying {} seconds before taking picture".format(self.cameraDelay))
			time.sleep(self.cameraDelay)

		super(PiCameraController, self).capture(
			output=output,
			format=format,
			use_video_port=use_video_port,
			resize=resize,
			splitter_port=splitter_port,
			**options
		)
		self.logger.debug("picture taken")
