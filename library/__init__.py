import logging


def setup_logging(logger, loggingLevel=False, logFile=None):
		"""
		Set up logging stream and file handlers
		@param logger: logger for the module/object we're setting up logging for
		@type logger: logging.Logger
		@param loggingLevel: logging level as defined by logging package
		@type loggingLevel: int
		@param logFile: (optional) path for file logging
		@type logFile: str
		@return: logger with handlers setup
		@rtype: logging.Logger
		"""
		logger.info("Logging level: {}".format('DEBUG' if loggingLevel else 'INFO'))

		# stdout stream handler
		streamHandler = logging.StreamHandler()
		streamHandler.setLevel(logging.DEBUG if loggingLevel else logging.INFO)

		# stdout logging formatting
		stdoutFormat = "%(name)s - %(levelname)s - %(message)s"
		stdoutFormatter = logging.Formatter(stdoutFormat)
		streamHandler.setFormatter(stdoutFormatter)

		# remove existing handlers then add the new one
		logger.handlers = []
		logger.addHandler(streamHandler)

		# set up file handler logger - always debug level
		if logFile:
			logger.info("Logging to file: {}".format(logFile))
			fileHandler = logging.FileHandler(logFile)
			fileHandler.setLevel(logging.DEBUG)

			# file logging formatting
			fileFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
			fileFormatter = logging.Formatter(fileFormat)
			fileHandler.setFormatter(fileFormatter)
			logger.addHandler(fileHandler)
		else:
			logger.warning("No log file path specified - file logging disabled")
		return logger
