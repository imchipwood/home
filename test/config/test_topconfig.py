
from library.config.topconfig import ConfigurationHandler
from library.config.environmentconfig import EnvironmentConfig


class TestClass(object):
	def test_getsensorconfig(self):
		configs = {
			EnvironmentConfig: "media_test.json"
		}
		for configtype, path in configs.items():
			config = ConfigurationHandler(path)

			sensorconfig = config.getsensorconfig('environment')
			assert isinstance(sensorconfig, configtype)
			del config
