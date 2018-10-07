

class EnvironmentController(object):
	def __init__(self, configpath, mqttconfig=None):
		super(EnvironmentController, self).__init__()

		self._configpath = configpath
		self._mqttconfig = mqttconfig
