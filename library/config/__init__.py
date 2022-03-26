from collections import OrderedDict
import json
import os
from typing import List, Type, Union, Dict

from library import CONFIG_DIR, TEST_CONFIG_DIR, CONFIG_TYPE, CONTROLLER_TYPE
# from library.data.database import


class SENSORCLASSES:
    ENVIRONMENT = "environment"
    MQTT_ENVIRONMENT = "mqtt_environment"
    GPIO_MONITOR = "gpio_monitor"
    GPIO_DRIVER = "gpio_driver"
    TIMER = "timer"
    CAMERA = "camera"
    PUSHBULLET = "pushbullet"


class BaseConfigKeys:
    MQTT = "mqtt"
    SENSORS = "sensors"
    LOG = "log"
    BROKER = "broker"
    PORT = "port"
    CLIENT_ID = "client_id"
    TOPICS = "topics"
    PUBLISH = "publish"
    SUBSCRIBE = "subscribe"
    NAME = "name"               # why did i make this key
    TABLE_NAME = "table_name"   # which table to write data received over mqtt to
    DELAY = "delay"
    PIN = "gpio_pin"
    DB = "db"
    DB_TABLES = "tables"
    DB_PATH = "path"
    DB_COLUMNS = "columns"
    DB_COLUMN_NAME = "col_name"
    DB_COLUMN_TYPE = "col_type"
    DB_COLUMN_KEY = "col_key"
    DB_FOREIGN_TABLE_KEY = "foreign_table_key"

    DB_SERVER = "server"
    DB_DATABASE = "database"
    DB_USERNAME = "username"
    DB_PASSWORD = "password"


class PubSubKeys:
    """
    Simple class to avoid using raw strings all over the place
    """
    PUBSUB = "pubsub"
    SUBSCRIBE = BaseConfigKeys.SUBSCRIBE
    PUBLISH = BaseConfigKeys.PUBLISH
    CAPTURE = "capture"
    CONTROL = "control"
    DELAY = BaseConfigKeys.DELAY
    FORCE = "force"
    BOTH = "both"
    PAYLOAD = "payload"
    STATE = "state"
    ID = "convo_id"


class DatabaseKeys:
    from library.config import PubSubKeys
    STATE = PubSubKeys.STATE
    ID = PubSubKeys.ID
    TIMESTAMP = "timestamp"
    CAPTURED = "captured"
    TOGGLED = "toggled"
    NOTIFIED = "notified"


class BaseConfiguration:
    """
    Base configuration class for all sensor/controller configs to derive from
    """
    from library.data.database import Column
    BASE_CONFIG_DIR = None

    def __init__(self: CONFIG_TYPE, config_path: str, debug: bool = False):
        """
        @param config_path: path to configuration file
        @type config_path: str
        @param debug: debug flag
        @type debug: bool
        """
        super()
        self.debug = debug

        self._config_path = ""
        self._config = {}
        self.config = config_path

    def __repr__(self) -> str:
        """
        @rtype: str
        """
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
            if not potential_dir:
                continue

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
        with open(config_path, "r") as inf:
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
        return self.config.get(BaseConfigKeys.SENSORS)

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
        return self.config.get(BaseConfigKeys.LOG, "")

    @property
    def db_enabled(self) -> bool:
        """
        Check if database writing/reading is enabled
        @return: whether db is enabled
        @rtype: bool
        """
        return bool(self.config.get(BaseConfigKeys.DB))

    @property
    def db_name(self) -> str:
        """
        @return: database name
        @rtype: str
        """
        db_path = self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_PATH)
        if not db_path:
            return ""
        return os.path.splitext(os.path.basename(db_path))[0]

    # def _get_table_definition(self, table_name: str) -> dict:
    #     """
    #     Get the dictionary of table information for the given table name
    #     @param table_name: name of database table
    #     @type table_name: str
    #     @return: dictionary of table information
    #     @rtype: dict
    #     """
    #     table_definitions = self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_TABLES)
    #     if not table_definitions:
    #         return {}
    #     for table_definition in table_definitions:
    #         if table_definition.get(BaseConfigKeys.TABLE_NAME) == table_name:
    #             return table_definition
    #     return {}
    #
    # def get_db_columns_for_table(self, table_name: str) -> Dict[str, List[Column]]:
    #     """
    #     Get a list of database Columns for the given table name
    #     @param table_name: name of database table
    #     @type table_name: str
    #     @return: the list of columns for the given table name
    #     @rtype: dict[str, list[Column]]
    #     """
    #     table_definition = self._get_table_definition(table_name)
    #     if not table_definition:
    #         return {}
    #     from library.data.database import Column
    #     columns = []
    #     for column_dict in table_definition.get(BaseConfigKeys.DB_COLUMNS, []):
    #         column = Column(
    #             column_dict.get(BaseConfigKeys.DB_COLUMN_NAME, ""),
    #             column_dict.get(BaseConfigKeys.DB_COLUMN_TYPE, ""),
    #             column_dict.get(BaseConfigKeys.DB_COLUMN_KEY, ""),
    #         )
    #         columns.append(column)
    #     return {table_name: columns}

    @property
    def db_tables(self) -> Dict[str, List[Column]]:
        """

        @return: dictionary of table names to columns
        @rtype: dict[str, list[Column]]
        """
        from library.data.database import Column
        table_definitions = self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_TABLES)
        tables = OrderedDict()
        for table_definition in table_definitions:
            table_name = table_definition.get(BaseConfigKeys.NAME)
            columns = []
            for column_dict in table_definition.get(BaseConfigKeys.DB_COLUMNS, []):
                column = Column(
                    column_dict.get(BaseConfigKeys.DB_COLUMN_NAME, ""),
                    column_dict.get(BaseConfigKeys.DB_COLUMN_TYPE, ""),
                    column_dict.get(BaseConfigKeys.DB_COLUMN_KEY, ""),
                    column_dict.get(BaseConfigKeys.DB_FOREIGN_TABLE_KEY),
                )
                columns.append(column)
            tables[table_name] = columns
        return tables

    @property
    def db_columns(self) -> List[Column]:
        """
        @return: list of database column objects
        @rtype: list[Column]
        """
        from library.data.database import Column
        column_data = self.config.get(BaseConfigKeys.DB)
        if not column_data:
            return []
        columns = []
        for column_dict in column_data.get(BaseConfigKeys.DB_COLUMNS, []):
            column = Column(
                column_dict.get(BaseConfigKeys.DB_COLUMN_NAME, ""),
                column_dict.get(BaseConfigKeys.DB_COLUMN_TYPE, ""),
                column_dict.get(BaseConfigKeys.DB_COLUMN_KEY, ""),
                column_dict.get(BaseConfigKeys.DB_FOREIGN_TABLE_KEY)
            )
            columns.append(column)
        return columns

    @property
    def db_server(self) -> str:
        """
        @return: server path (with port)
        @rtype: str
        """
        return self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_SERVER)

    @property
    def db_database_name(self) -> str:
        """
        @return: database name
        @rtype: str
        """
        return self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_DATABASE)

    @property
    def db_username(self) -> str:
        """
        @return: username
        @rtype: str
        """
        return self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_USERNAME)

    @property
    def db_password(self) -> str:
        """
        @return: database password
        @rtype: str
        """
        password = self.config.get(BaseConfigKeys.DB, {}).get(BaseConfigKeys.DB_PASSWORD, "")
        return os.environ.get(password[1:], "") if password.startswith("$") else password


class ConfigurationHandler(BaseConfiguration):

    # TODO: Update these as they're developed
    SENSOR_CLASS_LIST = [
        SENSORCLASSES.ENVIRONMENT,
        SENSORCLASSES.MQTT_ENVIRONMENT,
        SENSORCLASSES.GPIO_MONITOR,
        SENSORCLASSES.GPIO_DRIVER,
        SENSORCLASSES.CAMERA,
        # SENSORCLASSES.PUSHBULLET,
        SENSORCLASSES.TIMER
    ]
    from library.config.mqtt import MQTTConfig

    def __init__(self, config_path: str, debug: bool = False):
        """
        @param config_path: path to top-level configuration JSON file
        @type config_path: str
        @param debug: debug flag
        @type debug: bool
        """
        super().__init__(config_path, debug)
        self._current_sensor = 0
        self.sensorTypes = list(self.config.get(BaseConfigKeys.SENSORS, {}))
        self.sensors = {}

    # region Sensors

    @property
    def mqtt_config_path(self) -> str:
        """
        Get the full path to the base MQTT configuration file
        @return: path to the base MQTT configuration file
        """
        config_path = self.config.get(BaseConfigKeys.MQTT)
        if not config_path:
            return ""
        elif os.path.exists(config_path):
            return config_path

        return self.normalize_config_path(config_path)

    def get_sensor_mqtt_config(self, sensor) -> Union[MQTTConfig, None]:
        """
        Get the MQTT config class for the given sensor
        @param sensor: target sensor
        @type sensor: str
        @return: MQTT configuration object with sensor settings
        """
        from library.config.mqtt import MQTTConfig
        if sensor in self.sensor_paths:
            return MQTTConfig(self.mqtt_config_path, self.get_sensor_path(sensor), self.debug)

        return None  # pragma: no cover

    def get_sensor_config(self, sensor) -> Type[CONFIG_TYPE]:
        """
        Get the config class for the particular
        @param sensor: target sensor
        @type sensor: str
        @return: the sensor config object for the given sensor if supported
        """
        if not (sensor in self.SENSOR_CLASS_LIST and sensor in self.sensor_paths):
            return None

        if sensor == SENSORCLASSES.ENVIRONMENT:
            from library.config.environment import EnvironmentConfig
            sensor_cfg_cls = EnvironmentConfig
        elif sensor == SENSORCLASSES.CAMERA:
            from library.config.camera import CameraConfig
            sensor_cfg_cls = CameraConfig
        elif sensor == SENSORCLASSES.TIMER:
            from library.config.timer import TimerConfig
            sensor_cfg_cls = TimerConfig
        elif sensor == SENSORCLASSES.MQTT_ENVIRONMENT:
            from library.config.mqtt_environment import MqttEnvironmentConfig
            sensor_cfg_cls = MqttEnvironmentConfig
        elif sensor == SENSORCLASSES.GPIO_DRIVER:
            from library.config.gpio_driver import GPIODriverConfig
            sensor_cfg_cls = GPIODriverConfig
        elif sensor == SENSORCLASSES.GPIO_MONITOR:
            from library.config.gpio_monitor import GPIOMonitorConfig
            sensor_cfg_cls = GPIOMonitorConfig
        # elif sensor == SENSORCLASSES.PUSHBULLET:
        #     from library.config.pushbullet import PushbulletConfig
        #     sensor_cfg_cls = PushbulletConfig
        else:
            raise Exception(f"did not recognize sensor type {sensor}")

        return sensor_cfg_cls(
            self.sensor_paths[sensor],
            self.get_sensor_mqtt_config(sensor),
            self.debug
        )

    def get_sensor_controller(self, sensor) -> Type[CONTROLLER_TYPE]:
        """
        Get the sensor object for the given sensor
        @param sensor: target sensor
        @type sensor: str
        @return: sensor object
        """
        if sensor not in self.SENSOR_CLASS_LIST:
            return None

        if sensor in self.sensors:
            return self.sensors[sensor]

        # reduce need to import classes UNLESS that class is actually going to be used
        if sensor == SENSORCLASSES.ENVIRONMENT:
            from library.controllers.environment import EnvironmentController
            sensor_cls = EnvironmentController
        elif sensor == SENSORCLASSES.CAMERA:
            from library.controllers.camera import PiCameraController
            sensor_cls = PiCameraController
        elif sensor == SENSORCLASSES.TIMER:
            from library.controllers.timer import TimerController
            sensor_cls = TimerController
        elif sensor == SENSORCLASSES.MQTT_ENVIRONMENT:
            from library.controllers.mqtt_environment import MqttEnvironmentController
            sensor_cls = MqttEnvironmentController
        elif sensor == SENSORCLASSES.GPIO_DRIVER:
            from library.controllers.gpio_driver import GPIODriverController
            sensor_cls = GPIODriverController
        elif sensor == SENSORCLASSES.GPIO_MONITOR:
            from library.controllers.gpio_monitor import GPIOMonitorController
            sensor_cls = GPIOMonitorController
        else:
            # apparently actually NOT in the map...
            raise Exception(f"did not recognize sensor type {sensor}")

        self.sensors[sensor] = sensor_cls(self.get_sensor_config(sensor), self.debug)
        return self.sensors[sensor]

    # endregion Sensors
    # region BuiltIns

    def __repr__(self) -> str:
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
        for sensor in self.config.get(BaseConfigKeys.SENSORS, {}):
            yield self.get_sensor_controller(sensor)

    def __next__(self):  # pragma: no cover
        """
        Get the next sensor
        @return: sensor controller
        @rtype: library.controllers.BaseController
        """
        if self._current_sensor >= len(self.sensors):
            raise StopIteration

        sensor = self.sensorTypes[self._current_sensor]
        self._current_sensor += 1
        yield self.get_sensor_controller(sensor)

        # endregion BuiltIns
