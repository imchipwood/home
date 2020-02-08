import os
from typing import List
import sqlite3
from library import HOME_DIR
from library.controllers import Get_Logger

log_path = os.path.realpath(os.path.join(HOME_DIR, '..', 'logs', 'database.log'))
LOGGER = Get_Logger(__name__, debug_flag=True, log_path=log_path)


def get_database_path(name: str) -> str:
    """
    Get the path to the target database
    @param name: name of the database
    @type name: str
    @return: path to database file
    @rtype: str
    """
    data_dir = os.path.join(HOME_DIR, "data")
    database_path = os.path.join(data_dir, name + ".sqlite3")
    LOGGER.debug(f"Looking for database {database_path}")
    if not os.path.exists(data_dir):
        LOGGER.debug(f"Didn't find {database_path} - creating {data_dir}")
        os.makedirs(data_dir)
    return database_path


def connect_to_database(name: str) -> sqlite3.Connection:
    """
    Connect to target database
    @param name: name of database
    @type name: str
    @return: open database connection
    @rtype: sqlite3.Connection
    """
    con = sqlite3.connect(get_database_path(name))
    return con


class Column:
    def __init__(self, col_name: str, col_type: str, col_key: str):
        """
        Initialize a database column object
        @param col_name: name of column
        @type col_name: str
        @param col_type: data type of column
        @type col_type: str
        @param col_key: column key type
        @type col_key: str
        """
        super()
        self.name = col_name
        self.type = col_type
        self.key = col_key

    @property
    def primary(self) -> bool:
        """
        Check if this is a primary key column
        @return: whether or not this is a primary key column
        @rtype: bool
        """
        return self.key.upper() == "PRIMARY KEY"


class Database:
    def __init__(self, name: str, columns: List[Column]):
        """
        Initialize a database with a table
        @param name: name of database
        @type name: str
        @param columns: list of columns to use in tables
        @type columns: list[Column]
        """
        super()
        self.name = name
        self.columns = columns
        self.con = None
        self.cur = None

    def setup(self):
        """
        Set up the database with a table
        """
        self.con = connect_to_database(self.name)
        self.cur = self.con.cursor()
        if not self.does_table_exist(self.name):
            self.create_table(self.name, self.columns)

    @property
    def columns_str(self) -> str:
        """

        @return: column names in the table
        @rtype: str
        """
        return ', '.join([x.name for x in self.columns])

    def does_table_exist(self, table_name: str) -> bool:
        """
        Check if a table exists in the databalse
        @param table_name: name of table
        @type table_name: str
        @return: whether or not the table exists
        @rtype: bool
        """
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
        self.cur.execute(query)
        result = self.cur.fetchone()
        return result and result[0] == table_name

    def create_table(self, table_name: str, columns: List[Column]):
        """
        Create a table in the database
        @param table_name: name of the table
        @type table_name: str
        @param columns: list of columns to add to the table
        @type columns: list[Column]
        """
        print(f"Creating table {table_name}")
        assert columns, "Must define columns"
        query = f"CREATE TABLE {table_name} ("
        for column in columns:
            query += f"{column.name} {column.type} {column.key}, "
        query = query[:-2]
        query += ")"
        self.cur.execute(query)

    def add_data(self, data_to_add: List):
        """
        Add data to the table
        @param data_to_add: data to add to table
        @type data_to_add: list
        """
        query = f"INSERT INTO {self.name} ({self.columns_str}) VALUES ({', '.join(['?' for x in data_to_add])})"
        self.cur.execute(query, data_to_add)
        self.con.commit()

    def get_latest_record(self) -> List:
        """
        Get the latest record from the table
        @return: list of values from last record
        @rtype: list[int]
        """
        primary = [x.name for x in self.columns if x.primary][0]
        others = [x.name for x in self.columns if x.name != primary]
        others_str = ', '.join(others)
        query = f"SELECT MAX({primary}), {others_str} FROM {self.name}"
        self.cur.execute(query)
        result = self.cur.fetchone()
        return result

    def get_all_records(self) -> List:
        """
        Get all the records in the table
        @return: list of records
        @rtype: list
        """
        query = f"SELECT {self.columns_str} FROM {self.name}"
        self.cur.execute(query)
        result = self.cur.fetchall()
        return result

    def get_last_n_records(self, n: int):
        """
        Get the last n records from the table
        @param n: number of records to get
        @type n: int
        @return: last n records
        @rtype: list
        """
        primary = [x.name for x in self.columns if x.primary][0]
        query = f"SELECT * FROM (SELECT * FROM {self.name} ORDER BY {primary} DESC limit {n}) order by {primary} DESC"
        self.cur.execute(query)
        result = self.cur.fetchall()
        return result

    def delete_all_except_last_n_records(self, n: int):
        """
        Delete all records except the last n
        @param n: number of records to keep
        @type n: int
        """
        primary = [x.name for x in self.columns if x.primary][0]
        query = f"DELETE FROM {self.name} WHERE {primary} <= (SELECT MAX({primary}) " \
                f"FROM (SELECT {primary} FROM {self.name} ORDER BY {primary} LIMIT {n + 1}))"
        self.cur.execute(query)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        self.con.close()


if __name__ == "__main__":
    from random import randint
    import time
    db_name = "test2"
    db_columns = [
        Column("timestamp", "integer", "PRIMARY KEY"),
        Column("state", "integer", "NOT NULL")
    ]
    with Database(db_name, db_columns) as db:
        data = [int(time.time()), randint(0, 100)]
        print(f"Adding data: {data}")
        db.add_data(data)
        all_records = db.get_all_records()
        sorted_records = sorted(all_records, key=lambda x: x[0])
        print(all_records)
        print(sorted_records)
        print(db.get_last_n_records(2))

    print("done")
