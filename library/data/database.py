from abc import ABC, abstractmethod

from library.data import Column, DatabaseEntry
from typing import Dict, List


class BaseTable(ABC):
    def __init__(self, connection, name: str, columns: List[Column]):
        """
        Base table implementation
        @param connection: database connection - sqlite3.Connection or pyodbc.Connection
        @param name: name of table
        @type name: str
        @param columns:
        @type columns: list[Column]
        """
        super()
        self.connection = connection
        self.name = name
        self.columns = columns
        self.cursor = self.connection.cursor()
        self.setup()

    def setup(self):
        """
        Set up the database with a table
        """
        if not self.does_table_exist(self.name):
            self.create_table(self.name, self.columns)

    @abstractmethod
    def does_table_exist(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        @param table_name: name of table
        @type table_name: str
        @return: whether the table exists
        @rtype: bool
        """
        raise NotImplementedError

    @abstractmethod
    def create_table(self, table_name: str, columns: List[Column]):
        """
        Create a table in the database
        @param table_name: name of the table
        @type table_name: str
        @param columns: list of columns to add to the table
        @type columns: list[Column]
        """
        raise NotImplementedError

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

    @abstractmethod
    def add_data_multiple(self, data_to_add: List[List] or List[tuple]):
        """
        Add multiple rows the table at once
        @param data_to_add: multiple rows in a list
        """
        raise NotImplementedError

    @abstractmethod
    def add_data(self, data_to_add: List):
        """
        Add data to the table
        @param data_to_add: data to add to table
        @type data_to_add: list
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

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

    @abstractmethod
    def get_record(self, primary_key_value: int or float or str) -> DatabaseEntry:
        """
        Get the target record
        @param primary_key_value: value of the primary column corresponding to the target entry
        @type primary_key_value: int or float or str
        @return: DatabaseEntry for the target row
        @rtype: DatabaseEntry
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest_record(self) -> DatabaseEntry or None:
        """
        Get the latest record from the table
        @return: last record in the table
        @rtype: DatabaseEntry or None
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_records(self) -> List[DatabaseEntry]:
        """
        Get all the records in the table
        @return: list of records
        @rtype: list[DatabaseEntry]
        """
        raise NotImplementedError

    @abstractmethod
    def get_last_n_records(self, n: int):
        """
        Get the last n records from the table
        @param n: number of records to get
        @type n: int
        @return: last n records
        @rtype: list[DatabaseEntry]
        """
        raise NotImplementedError

    @abstractmethod
    def delete_all_except_last_n_records(self, n: int):
        """
        Delete all records except the last n
        @param n: number of records to keep
        @type n: int
        """
        raise NotImplementedError

    @abstractmethod
    def drop(self):
        """
        Delete the table
        """
        raise NotImplementedError


class BaseDatabase(ABC):
    TABLE_CLASS = None

    def __init__(self, tables: Dict[str, List[Column]]):
        super()
        self.table_definitions = tables
        self.tables = {}  # type: dict[str, BaseTable]
        self.connection = None

    def create_tables(self):
        """
        Create tables based on given definitions
        """
        if self.tables or not self.TABLE_CLASS:
            return
        for table_name, columns in self.table_definitions.items():
            self.tables[table_name] = self.TABLE_CLASS(self.connection, table_name, columns)

    def get_table(self, table_name: str) -> BaseTable or None:
        """
        Get a table by name
        @param table_name: name of table
        @type table_name: str
        @return: Table if found, else None
        @rtype: Table or None
        """
        return self.tables.get(table_name)

    @abstractmethod
    def connect(self):
        """
        Connect to the database
        """
        raise NotImplementedError

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        self.connection.close()
