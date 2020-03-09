import json
import os
import sqlite3
from typing import List

from library import HOME_DIR


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
    if not os.path.exists(data_dir):
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

    def __repr__(self) -> str:
        """
        @rtype: str
        """
        return f"{self.name} {self.type} {self.key}"


class DatabaseEntry:
    def __init__(self, columns: List[Column], entry):
        super()
        self.columns = columns
        self.entry = entry
        self._values = {}

    @property
    def values(self):
        """
        @return: dict of values
        @rtype: dict[str, int or float or str]
        """
        if not self._values:
            for i in range(len(self.entry)):
                self._values[self.columns[i].name] = self.entry[i]
        return self._values

    def __getitem__(self, item) -> int or float or str:
        return self.values.get(item)

    def __repr__(self) -> str:
        return json.dumps(self._values)


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

    def does_table_exist(self, table_name: str) -> bool:
        """
        Check if a table exists in the databalse
        @param table_name: name of table
        @type table_name: str
        @return: whether or not the table exists
        @rtype: bool
        """
        query = f"""
SELECT name FROM sqlite_master
WHERE type='table'
AND name='{table_name}';
"""
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
        assert table_name, "Must define table name"
        assert columns and all([isinstance(x, Column) for x in columns]), "Must define columns"
        print(f"Creating table {table_name}")
        query = f"CREATE TABLE {table_name} ({', '.join([str(x) for x in columns])})"
        self.cur.execute(query)

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
        self.cur.execute(query, data_to_add)
        self.con.commit()

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
        self.cur.execute(query)
        self.con.commit()

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
        return [DatabaseEntry(self.columns, result) for result in results]

    def get_record(self, primary_key_value: int or float or str) -> DatabaseEntry:
        """
        Get the target record
        @param primary_key_value: value of the primary column corresponding to the target entry
        @type primary_key_value: int or float or str
        @return: DatabaseEntry for the target row
        @rtype: DatabaseEntry
        """
        query = f"""SELECT * FROM {self.name} WHERE {self.primary_column_name} = {primary_key_value}"""
        self.cur.execute(query)
        result = self.cur.fetchone()
        return self.convert_query_result_to_database_entry(result)

    def get_latest_record(self) -> DatabaseEntry:
        """
        Get the latest record from the table
        @return: list of values from last record
        @rtype: DatabaseEntry
        """
        primary = [x.name for x in self.columns if x.primary][0]
        others = [x.name for x in self.columns if x.name != primary]
        others_str = ", ".join(others)
        query = f"SELECT MAX({self.primary_column_name}), {others_str} FROM {self.name}"
        self.cur.execute(query)
        result = self.cur.fetchone()
        return self.convert_query_result_to_database_entry(result)

    def get_all_records(self) -> List[DatabaseEntry]:
        """
        Get all the records in the table
        @return: list of records
        @rtype: list[DatabaseEntry]
        """
        query = f"SELECT {self.columns_str} FROM {self.name}"
        self.cur.execute(query)
        results = self.cur.fetchall()
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
SELECT * FROM (
  SELECT * 
  FROM {self.name}
  ORDER BY {primary} DESC
  LIMIT {n}
) ORDER BY {primary} DESC
"""
        self.cur.execute(query)
        results = self.cur.fetchall()
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
  WHERE {primary} <= (
    SELECT {primary}
    FROM (
      SELECT {primary}
      FROM {self.name}
      ORDER BY {primary} DESC
      LIMIT 1 OFFSET {n}
    )
  )
"""
        self.cur.execute(query)
        self.con.commit()

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
