from library.config import BaseConfiguration


class PushbulletConfig(BaseConfiguration):
    def __init__(self, config_path):
        super(PushbulletConfig, self).__init__(config_path)

    @property
    def api_key(self):
        return self.config.get("api")

    @property
    def notify(self):
        return self.config.get("notify")
