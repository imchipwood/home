import datetime
import logging
import os
import pyodbc
import sys
from typing import List, Dict

from library import HOME_DIR
from library.data import Column, DatabaseEntry


def get_database_path(name: str) -> str:
    """
    Get the path to the target database
    @param name: name of the database
    @type name: str
    @return: path to database file
    @rtype: str
    """
    data_dir = os.path.join(HOME_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    database_path = os.path.join(data_dir, os.path.basename(name) + ".sqlite3")
    return database_path


# def connect_to_database(path_or_name: str) -> sqlite3.Connection:
#     """
#     Connect to target database
#     @param name: name of database
#     @type name: str
#     @return: open database connection
#     @rtype: sqlite3.Connection
#     """
#     if ".sqlite3" not in path_or_name.lower():
#         path_or_name = get_database_path(path_or_name)
#
#     try:
#         con = sqlite3.connect(path_or_name)
#     except Exception as e:
#         logging.exception(f"Failed to connect to DB @ {path_or_name}")
#         raise e
#
#     return con


def connect_to_database_server(server_location: str, database_name: str, user: str, pw: str) -> pyodbc.Connection:
    """
    Connect to an SQL server
    @param server_location: server path
    @type server_location: str
    @param database_name: name of database
    @type database_name: str
    @param user: username
    @type user: str
    @param pw: password
    @type pw: str
    @return: connection to database
    @rtype: pyodbc.Connection
    """
    # linux_driver = "/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.0.so.1.1"
    linux_driver = "FreeTDS"
    win_driver = "SQL_SERVER"
    driver = win_driver
    if "linux" in sys.platform:
        driver = linux_driver
    connector = f"DRIVER={{{driver}}};" \
                f"SERVER={server_location};" \
                f"DATABASE={database_name};" \
                f"UID={user};" \
                f"PWD={pw}"
    try:
        connection = pyodbc.connect(connector)
        return connection
    except:
        logging.exception(f"Failed to connect to db {server_location}, {database_name} as '{user}'")
        raise


class Table:
    def __init__(self, connection: pyodbc.Connection, name: str, columns: List[Column]):
        super()
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.name = name  # table name
        self.columns = columns  # columns in the table
        self.setup()

    def setup(self):
        """
        Set up the database with a table
        """
        if not self.does_table_exist(self.name):
            self.create_table(self.name, self.columns)

    def does_table_exist(self, table_name: str) -> bool:
        """
        Check if a table exists in the databalse
        @param table_name: name of table
        @type table_name: str
        @return: whether or not the table exists
        @rtype: bool
        """
        query = f"""
SELECT name FROM sys.tables WHERE name='{table_name}';
"""
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result and result[0] == table_name

    def create_table(self, table_name: str, columns: List[Column]):
        """
        Create a table in the database
        @param table_name: name of the table
        @type table_name: str
        @param columns: list of columns to add to the table
        @type columns: list[Column]
        """
        assert table_name, "Must define table name"
        assert columns and all([isinstance(x, Column) for x in columns]), "Must define columns"
        # self.logger.debug(f"Creating table {table_name}")
        # iterate over non-foreign keys first
        query = f"CREATE TABLE {table_name} ({', '.join([str(x) for x in columns])}"
        for column in columns:
            query += column.get_table_reference()
        query += ")"
        self.cursor.execute(query)

    @property
    def primary_column_name(self) -> str:
        """
        Get the primary column name
        @rtype: str
        """
        return [x.name for x in self.columns if x.primary][0]

    @property
    def columns_str(self) -> str:
        """
        Columns as a string
        @return: column names in the table
        @rtype: str
        """
        return ", ".join([x.name for x in self.columns])

    def format_data_for_insertion(self, **kwargs) -> List:
        """
        Take keyword args and format them for db insertion
        @param kwargs: keyword args
        @type kwargs: dict
        @return: list of values for insertion
        @rtype: List
        """
        formatted_data = []
        for column in self.columns:
            val = kwargs.get(column.name, None)
            if val is None:
                raise Exception(f"Data for {column.name} was not passed in!")
            formatted_data.append(val)
        return formatted_data

    def add_data_multiple(self, data_to_add: List[List] or List[tuple]):
        """
        Add multiple rows the table at once
        @param data_to_add: multiple rows in a list
        """
        query = f"""
INSERT INTO {self.name} (
  {self.columns_str}
) VALUES (
  {', '.join(['?' for x in data_to_add[0]])}
)
"""
        self.cursor.executemany(query, data_to_add)
        self.connection.commit()

    def add_data(self, data_to_add: List):
        """
        Add data to the table
        @param data_to_add: data to add to table
        @type data_to_add: list
        """
        query = f"""
INSERT INTO {self.name} (
  {self.columns_str}
) VALUES (
  {', '.join(['?' for x in data_to_add])}
)
"""
        self.cursor.execute(query, data_to_add)
        self.connection.commit()

    def update_record(self, primary_key_value: int or float or str, column_name: str, new_value: int or float or str):
        """
        Update a record in the database
        @param primary_key_value: value of the primary column corresponding to the target entry
        @type primary_key_value: int or float or str
        @param column_name: name of the column to update
        @type column_name: str
        @param new_value: new value for the column
        @type new_value: int or float or str
        """
        query = f"""
UPDATE {self.name}
SET {column_name} = {new_value}
WHERE {self.primary_column_name} = {primary_key_value}
"""
        self.cursor.execute(query)
        self.connection.commit()

    def convert_query_result_to_database_entry(self, result: List) -> DatabaseEntry:
        """
        Convert a single query
        result into a DatabaseEntry object
        @param result: list of values from table entry
        @type result: list
        @return: DatabaseEntry object
        @rtype: DatabaseEntry
        """
        return DatabaseEntry(self.columns, result)

    def convert_query_results_to_database_entries(self, results: List) -> List[DatabaseEntry]:
        """
        Convert multiple query results into a list of DatabaseEntry objects
        @param results: list of lists of table entry values
        @type results: list[list]
        @return: list of DatabaseEntry objects
        @rtype: list[DatabaseEntry]
        """
        return [self.convert_query_result_to_database_entry(result) for result in results]

    def get_record(self, primary_key_value: int or float or str) -> DatabaseEntry:
        """
        Get the target record
        @param primary_key_value: value of the primary column corresponding to the target entry
        @type primary_key_value: int or float or str
        @return: DatabaseEntry for the target row
        @rtype: DatabaseEntry
        """
        query = f"""SELECT * FROM {self.name} WHERE {self.primary_column_name} = {primary_key_value}"""
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if not result:
            return None
        return self.convert_query_result_to_database_entry(result)

    def get_latest_record(self) -> DatabaseEntry or None:
        """
        Get the latest record from the table
        @return: last record in the table
        @rtype: DatabaseEntry or None
        """
        primary = [x.name for x in self.columns if x.primary][0]
        others = [x.name for x in self.columns if x.name != primary]
        others_str = ", ".join(others)
        query = f"SELECT TOP 1 {primary}, {others_str} FROM {self.name} ORDER BY {primary} DESC"
        self.cursor .execute(query)
        result = self.cursor.fetchone()
        if result is None:
            return None
        return self.convert_query_result_to_database_entry(result)

    def get_all_records(self) -> List[DatabaseEntry]:
        """
        Get all the records in the table
        @return: list of records
        @rtype: list[DatabaseEntry]
        """
        query = f"SELECT {self.columns_str} FROM {self.name}"
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return self.convert_query_results_to_database_entries(results)

    def get_last_n_records(self, n: int):
        """
        Get the last n records from the table
        @param n: number of records to get
        @type n: int
        @return: last n records
        @rtype: list[DatabaseEntry]
        """
        primary = [x.name for x in self.columns if x.primary][0]
        query = f"""
SELECT TOP {n} * 
FROM {self.name}
ORDER BY {primary} DESC
"""
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return self.convert_query_results_to_database_entries(results)

    def delete_all_except_last_n_records(self, n: int):
        """
        Delete all records except the last n
        @param n: number of records to keep
        @type n: int
        """
        primary = [x.name for x in self.columns if x.primary][0]
        query = f"""
DELETE FROM {self.name}
  WHERE {primary} NOT IN (
    SELECT TOP {n} {primary}
    FROM {self.name}
    ORDER BY {primary} DESC
  ) 
"""
        self.cursor.execute(query)
        self.connection.commit()

    def drop(self):
        """
        Delete the table
        """
        foreign_keys = {x.name for x in self.columns if x.foreign_table}
        # if any(foreign_keys):
        #     for key in foreign_keys:
        #         self.cursor.execute(f"ALTER TABLE {self.name} DROP CONSTRAINT {key}")
        #         self.cursor.execute()
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.name}")
        self.cursor.commit()


class Database:

    def __init__(self, tables: Dict[str, List[Column]], server, database, username, password):
        """
        Initialize a database with a table
        @param tables: dictionary of table name to columns
        @type tables: dict[str, list[Column]]
        @param server: path to server
        @type server: str
        @param database: database name
        @type database: str
        @param username: username to connect to db
        @type username: str
        @param password: password to connect to db
        @type password:
        """
        # from library.controllers import get_logger
        super()
        self.table_definitions = tables
        self.tables = {}  # type: dict[str, Table]
        self.connection = None  # type: pyodbc.Connection

        self.server = server
        self.database = database
        self.username = username
        self.__password = password

    def create_tables(self):
        """
        Create tables based on given definitions
        """
        if self.tables:
            return
        for table_name, columns in self.table_definitions.items():
            self.tables[table_name] = Table(self.connection, table_name, columns)

    def get_table(self, table_name: str) -> Table or None:
        """
        Get a table by name
        @param table_name: name of table
        @type table_name: str
        @return: Table if found, else None
        @rtype: Table or None
        """
        return self.tables.get(table_name)

    def connect(self):
        """
        Connect to the database
        """
        self.connection = connect_to_database_server(
            self.server,
            self.database,
            self.username,
            self.__password
        )
        self.create_tables()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        self.connection.close()


if __name__ == "__main__":
    from collections import OrderedDict
    from random import randint
    import time

    db_name = "test2"
    table1_name = "table1"
    table2_name = "table2"
    table1 = {
        table1_name: [
            Column("timestamp", "datetime", "PRIMARY KEY"),
            Column("state", "int", "NOT NULL"),
            Column("id", "varchar(50)", "NOT NULL", table2_name)
        ]
    }
    table2 = {
        table2_name: [
            Column("id", "varchar(50)", "PRIMARY KEY"),
            Column("meta", "text", "NOT NULL")
        ]
    }
    db_tables = OrderedDict()
    db_tables.update(table2)
    db_tables.update(table1)

    server = 'localhost,1433'
    database = 'model'
    username = 'sa'
    password = 'Ch1ck#nG0ose'

    with Database(db_tables, server, database, username, password) as db:

        table2 = db.get_table(table2_name)
        for i in range(3):
            data = [str(i), f"some metadata for {i}"]
            print(f"Adding to table2: {data}")
            table2.add_data(data)

        # all_records = table2.get_all_records()
        # sorted_records = sorted(all_records, key=lambda x: x[0])
        # print(all_records)
        # print(sorted_records)

        for _ in range(10):
            for i in range(3):
                tmp_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f").split(".")
                timestamp = tmp_timestamp[0] + "." + tmp_timestamp[1][:3]
                data = [timestamp, randint(0, 100), str(i)]
                print(f"Adding to table1: {data}")
                table = db.get_table(table1_name)
                table.add_data(data)
                time.sleep(0.1)
        all_records = table.get_all_records()
        # sorted_records = sorted(all_records, key=lambda x: x[0])
        # print(all_records)
        # print(sorted_records)
        # print(db.get_last_n_records(2))

    print("done")
