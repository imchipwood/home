import json
import os
from typing import List

from library import CONFIG_DIR, TEST_CONFIG_DIR
from library.controllers.camera import PiCameraController
from library.controllers.environment import EnvironmentController
from library.controllers.gpio_monitor import GPIOMonitorController
from library.controllers.pushbullet import PushbulletController
from library.data.database import Column


class SENSORCLASSES:
    ENVIRONMENT = "environment"
    GPIO_MONITOR = "gpio_monitor"
    GPIO_DRIVER = "gpio_driver"
    CAMERA = "camera"
    PUSHBULLET = "pushbullet"


class ConfigKeys:
    MQTT = 'mqtt'
    SENSORS = 'sensors'
    LOG = 'log'
    BROKER = 'broker'
    PORT = 'port'
    CLIENT_ID = 'client_id'
    TOPICS = 'topics'
    PUBLISH = 'publish'
    SUBSCRIBE = 'subscribe'
    DB = 'db'
    DB_NAME = 'name'
    DB_COLUMNS = 'columns'
    DB_COLUMN_NAME = 'col_name'
    DB_COLUMN_TYPE = 'col_type'
    DB_COLUMN_KEY = 'col_key'


class BaseConfiguration:
    # By assuming the
    BASE_CONFIG_DIR = None

    def __init__(self, config_path, debug=False):
        """
        @param config_path: path to configuration file
        @type config_path: str
        @param debug: debug flag
        @type debug: bool
        """
        super()
        self.config_keys = ConfigKeys
        self.debug = debug

        self._config_path = ""
        self._config = {}
        self.config = config_path

    def __repr__(self):
        return json.dumps(self.config, indent=2)

    @classmethod
    def normalize_config_path(cls, config_path) -> str:
        """
        Normalize a config file path to the config dir of the repo
        @param config_path: relative or absolute config path
        @type config_path: str
        @return: normalized, absolute config path
        @rtype: str
        """
        assert config_path, "No path provided"

        # If path is absolute and exists, return it
        if os.path.exists(config_path):
            base_dir = os.path.dirname(config_path)
            if BaseConfiguration.BASE_CONFIG_DIR != base_dir:
                BaseConfiguration.BASE_CONFIG_DIR = base_dir
                print(f"New base configuration directory: {base_dir}")
            return config_path

        # Path doesn't exist (might be relative)
        # Iterate over potential directories
        potential_dirs = [
            BaseConfiguration.BASE_CONFIG_DIR,
            CONFIG_DIR,
            TEST_CONFIG_DIR
        ]
        for potential_dir in potential_dirs:
            # BASE_CONFIG_DIR could not be set yet
            if potential_dir:
                # if the path exists, save the base dir for next time and return it
                potential_path = os.path.join(potential_dir, config_path)
                if os.path.exists(potential_path):
                    BaseConfiguration.BASE_CONFIG_DIR = potential_dir
                    return potential_path

        # Can't figure out path - exit
        raise OSError(f"Could not find config file {config_path} at base dir {BaseConfiguration.BASE_CONFIG_DIR}")  # pragma: no cover

    @staticmethod
    def load_config(config_path) -> dict:
        """
        Parse a config file
        @param config_path: path to config file
        @type config_path: str
        @return: data from config file
        @rtype: dict
        """
        with open(config_path, 'r') as inf:
            return json.load(inf)

    @property
    def config(self) -> dict:
        """
        Get the current config dict
        @return: current config dict
        @rtype: dict
        """
        return self._config

    @config.setter
    def config(self, config_path):
        """
        Set a new config using a path to a JSON file
        @param config_path: path to config file
        @type config_path: str
        """
        if not config_path:
            return

        config_path = self.normalize_config_path(config_path)
        self._config_path = config_path
        self._config = self.load_config(self._config_path)

    @property
    def sensor_paths(self) -> dict:
        """
        Get the sensor config path dict
        @return: dict of sensor config paths
        @rtype: dict[str, str]
        """
        return self.config.get(ConfigKeys.SENSORS)

    def get_sensor_path(self, sensor) -> str:
        """
        Get the config path for the target sensor
        @param sensor: target sensor
        @type sensor: str
        @return: Path to sensor config
        @rtype: str
        """
        return self.normalize_config_path(self.sensor_paths.get(sensor))

    @property
    def log(self) -> str:
        """
        @return: Path to log file
        @rtype: str
        """
        return self.config.get(ConfigKeys.LOG, "")

    @property
    def db_name(self) -> str:
        """
        @return: database name
        @rtype: str
        """
        column_data = self.config.get(ConfigKeys.DB)
        if not column_data:
            return ""
        return column_data.get(ConfigKeys.DB_NAME)

    @property
    def db_columns(self) -> List[Column]:
        """
        @return: list of database column objects
        @rtype: list[Column]
        """
        column_data = self.config.get(ConfigKeys.DB)
        if not column_data:
            return []
        columns = []
        for column_dict in column_data.get(ConfigKeys.DB_COLUMNS, []):
            column = Column(
                column_dict.get(ConfigKeys.DB_COLUMN_NAME, ""),
                column_dict.get(ConfigKeys.DB_COLUMN_TYPE, ""),
                column_dict.get(ConfigKeys.DB_COLUMN_KEY, ""),
            )
            columns.append(column)
        return columns


class ConfigurationHandler(BaseConfiguration):
    # Import all the sensor-specific configuration objects
    from library.config.environment import EnvironmentConfig
    from library.config.gpio_monitor import GPIOMonitorConfig
    from library.config.camera import CameraConfig
    from library.config.pushbullet import PushbulletConfig

    # TODO: Update these as they're developed
    SENSOR_CLASS_MAP = {
        SENSORCLASSES.ENVIRONMENT: EnvironmentController,
        SENSORCLASSES.GPIO_MONITOR: GPIOMonitorController,
        SENSORCLASSES.GPIO_DRIVER: None,
        SENSORCLASSES.CAMERA: PiCameraController,
        SENSORCLASSES.PUSHBULLET: PushbulletController,
    }
    SENSOR_CONFIG_CLASS_MAP = {
        SENSORCLASSES.ENVIRONMENT: EnvironmentConfig,
        SENSORCLASSES.GPIO_MONITOR: GPIOMonitorConfig,
        SENSORCLASSES.GPIO_DRIVER: None,
        SENSORCLASSES.CAMERA: CameraConfig,
        SENSORCLASSES.PUSHBULLET: PushbulletConfig,
    }

    def __init__(self, config_path, debug=False):
        """
        @param config_path: path to top-level configuration JSON file
        @type config_path: str
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config_path, debug)
        self._current_sensor = 0
        self.sensorTypes = list(self.config.get(ConfigKeys.SENSORS, {}))
        self.sensors = {}

    # region Sensors

    @property
    def mqtt_config_path(self) -> str:
        """
        Get the full path to the base MQTT configuration file
        @return: path to the base MQTT configuration file
        @rtype: str
        """
        config_path = self.config.get(ConfigKeys.MQTT)
        if not config_path:
            return ""
        elif os.path.exists(config_path):
            return config_path
        else:
            return self.normalize_config_path(config_path)

    def get_sensor_mqtt_config(self, sensor):
        """
        Get the MQTT config class for the given sensor
        @param sensor: target sensor
        @type sensor: str
        @return: MQTT configuration object with sensor settings
        @rtype: MQTTConfig
        """
        from library.config.mqtt import MQTTConfig
        if sensor in self.sensor_paths:
            return MQTTConfig(self.mqtt_config_path, self.get_sensor_path(sensor), self.debug)
        else:
            return None  # pragma: no cover

    def get_sensor_config(self, sensor):
        """
        Get the config class for the particular
        @param sensor: target sensor
        @type sensor: str
        @return: the sensor config object for the given sensor if supported
        @rtype: library.config.BaseConfiguration
        """
        if sensor in self.SENSOR_CONFIG_CLASS_MAP and sensor in self.sensor_paths:
            return self.SENSOR_CONFIG_CLASS_MAP[sensor](
                self.sensor_paths[sensor],
                self.get_sensor_mqtt_config(sensor),
                self.debug
            )
        else:
            return None  # pragma: no cover

    def get_sensor_controller(self, sensor):
        """
        Get the sensor object for the given sensor
        @param sensor: target sensor
        @type sensor: str
        @return: sensor object
        @rtype: library.controllers.BaseController
        """
        if sensor in self.SENSOR_CLASS_MAP:
            if sensor not in self.sensors:
                self.sensors[sensor] = self.SENSOR_CLASS_MAP[sensor](self.get_sensor_config(sensor), self.debug)
            return self.sensors[sensor]
        else:
            return None  # pragma: no cover

    # endregion Sensors
    # region BuiltIns

    def __repr__(self):
        """
        @rtype: str
        """
        return f"({', '.join(self.sensorTypes)})"

    def __iter__(self):
        """
        Yield a sensor one at a time
        @return: sensor controllers iteratively
        """
        self._current_sensor = 0
        for sensor in self.config.get(ConfigKeys.SENSORS, {}):
            yield self.get_sensor_controller(sensor)

    def __next__(self):  # pragma: no cover
        """
        Get the next sensor
        @return: sensor controller
        @rtype: library.controllers.BaseController
        """
        if self._current_sensor < len(self.sensors):
            sensor = self.sensorTypes[self._current_sensor]
            self._current_sensor += 1
            return self.get_sensor_controller(sensor)
        else:
            raise StopIteration

        # endregion BuiltIns
