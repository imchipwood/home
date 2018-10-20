from inspect import ismethod

from library.config.topconfig import ConfigurationHandler
from library.config.environmentconfig import EnvironmentConfig
from library.controllers.environmentcontroller import EnvironmentController


def test_getsensorconfig():
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

			# Check the class is as expected
			assert isinstance(config, configclass)

			# Kill it
			del confighandler


def test_getsensorcontroller():
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

			# Check the class is as expected
			assert isinstance(controller, controllerclass)

			# Check all the methods are defined
			assert ismethod(controller.loop)
			assert ismethod(controller.start)
			assert ismethod(controller.stop)
			assert ismethod(controller.cleanup)

			# Kill it
			del confighandler
