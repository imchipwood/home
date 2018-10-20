
from library.config.topconfig import ConfigurationHandler
from library.config.environmentconfig import EnvironmentConfig
from library.controllers.environmentcontroller import EnvironmentController


class TestClass(object):
	def test_getsensorconfig(self):
		configs = {
			"environment": {
				EnvironmentConfig: "media_test.json"
			},
			# "door": {
			# 	DoorConfig: "door_test.json"
			# }
		}
		for configtype, configdict in configs.items():
			for configclass, path in configdict.items():
				confighandler = ConfigurationHandler(path)

				config = confighandler.getsensorconfig(configtype)
				assert isinstance(config, configclass)
				del confighandler

	def test_getsensorcontroller(self):
		configs = {
			"environment": {
				EnvironmentController: "media_test.json"
			},
			# "door": {
			# 	DoorController: "door_test.json"
			# }
		}
		for configtype, configdict in configs.items():
			for controllerclass, path in configdict.items():
				confighandler = ConfigurationHandler(path)

				controller = confighandler.getsensorcontroller(configtype)
				controller.stop()
				assert isinstance(controller, controllerclass)
				del confighandler
