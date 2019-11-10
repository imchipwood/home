import os
from typing import List
import sqlite3
from library import HOME_DIR


def get_database_path(name: str) -> str:
    data_dir = os.path.join(HOME_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    database_path = os.path.join(data_dir, name + ".sqlite3")
    return database_path


def connect_to_database(name: str):
    con = sqlite3.connect(get_database_path(name))
    return con


class Column:
    def __init__(self, col_name: str, col_type: str, col_key: str):
        super()
        self.name = col_name
        self.type = col_type
        self.key = col_key

    @property
    def primary(self) -> bool:
        return self.key.upper() == "PRIMARY KEY"


class Database:
    def __init__(self, name: str, columns):
        super()
        self.name = name
        self.columns = columns

    def columns_str(self):
        return ', '.join([x.name for x in self.columns])

    def does_table_exist(self, table_name: str) -> bool:
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
        self.cur.execute(query)
        result = self.cur.fetchone()
        return result and result[0] == table_name

    def create_table(self, table_name: str, columns: List[Column]):
        print(f"Creating table {table_name}")
        assert columns, "Must define columns"
        query = f"CREATE TABLE {table_name} ("
        for column in columns:
            query += f"{column.name} {column.type} {column.key}, "
        query = query[:-2]
        query += ")"
        self.cur.execute(query)

    def add_data(self, data):
        query = f"INSERT INTO {self.name} ({self.columns_str()}) VALUES ({', '.join(['?' for x in data])})"
        self.cur.execute(query, data)
        self.con.commit()

    def get_latest_record(self):
        primary = [x.name for x in self.columns if x.primary][0]
        others = [x.name for x in self.columns if x.name != primary]
        others_str = ', '.join(others)
        query = f"SELECT MAX({primary}), {others_str} FROM {self.name}"
        self.cur.execute(query)
        result = self.cur.fetchone()
        return result

    def __enter__(self):
        self.con = connect_to_database(self.name)
        self.cur = self.con.cursor()
        if not self.does_table_exist(self.name):
            self.create_table(self.name, self.columns)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()


if __name__ == "__main__":
    from random import randint
    import time
    db_name = "test"
    db_columns = [
        Column("timestamp", "integer", "PRIMARY KEY"),
        Column("state", "integer", "NOT NULL")
    ]
    with Database(db_name, db_columns) as db:
        data = [int(time.time()), randint(0, 100)]
        print(f"Adding data: {data}")
        db.add_data(data)
        print(db.get_latest_record())

    print("done")
