import json


class PushbulletConfig(object):
    def __init__(self, configPath):
        super(PushbulletConfig, self).__init__()

        self.configPath = configPath
        self._config = self.loadConfig(self.configPath)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, configPath):
        self._config = self.loadConfig(configPath)

    @property
    def apiKey(self):
        return self._config.get("api")

    def loadConfig(self, configPath):
        with open(configPath, 'r') as inf:
            return json.load(inf)
