import os
from typing import List

import pytest

from library.data.database import Column, Database, get_database_path

DB0_NAME = "PITEST_DB0"
DB1_NAME = "PITEST_DB1"
DB0_COLUMNS = [
    Column("timestamp", "integer", "PRIMARY KEY"),
    Column("state", "integer", "NOT NULL"),
    Column("notified", "integer", "NOT NULL")
]
DB1_COLUMNS = [
    Column("timestamp", "integer", "PRIMARY KEY"),
    Column("state", "string", "NOT NULL"),
    Column("notified", "integer", "NOT NULL")
]


def remove_db():
    """
    Remove all databases
    """
    for db_name in [DB0_NAME, DB1_NAME]:
        db_path = get_database_path(db_name)
        if os.path.exists(db_path):
            os.remove(db_path)


def setup_function():
    remove_db()


@pytest.mark.parametrize("name,columns", [
    (DB0_NAME, DB0_COLUMNS),
    (DB1_NAME, DB1_COLUMNS)
])
def test_create_table(name: str, columns: List[Column]):
    """
    Test creating table works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: list[Column]
    """
    with Database(name, columns) as db:
        assert os.path.exists(get_database_path(name))
        assert db.does_table_exist(name)


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, 0),
    (DB1_NAME, DB1_COLUMNS, "hello")
])
def test_add_to_table(name: str, columns: List[Column], data_to_add: int or str):
    """
    Test adding info to tables work
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: int or str
    """
    with Database(name, columns) as db:
        db.add_data([0, data_to_add, int(False)])
        db.add_data([1, data_to_add, int(False)])
        db.add_data([2, data_to_add, int(False)])

        assert len(db.get_all_records()) == 3


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_get_last_n_records(name, columns, data_to_add):
    """
    Test getting last n records from table works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: int or str
    """
    with Database(name, columns) as db:
        for i in range(len(data_to_add)):
            db.add_data([i, data_to_add[i], int(False)])

        assert len(db.get_last_n_records(1)) == 1
        assert len(db.get_last_n_records(2)) == 2
        last_3 = db.get_last_n_records(3)
        assert last_3[0][columns[0].name] == 4
        assert last_3[0][columns[1].name] == data_to_add[-1]
        assert last_3[1][columns[0].name] == 3
        assert last_3[1][columns[1].name] == data_to_add[-2]
        assert last_3[2][columns[0].name] == 2
        assert last_3[2][columns[1].name] == data_to_add[-3]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_get_latest_record(name, columns, data_to_add):
    """
    Test getting latest table record works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: int or str
    """
    with Database(name, columns) as db:
        for i in range(len(data_to_add)):
            db.add_data([i, data_to_add[i], int(False)])

        latest = db.get_latest_record()
        assert latest[columns[0].name] == 4
        assert latest[columns[1].name] == data_to_add[-1]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_delete_all_except_last_n_records(name, columns, data_to_add):
    """
    Test removing all but last N records from table works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: int or str
    """
    with Database(name, columns) as db:
        for i in range(len(data_to_add)):
            db.add_data([i, data_to_add[i], int(False)])

        for i in range(5, 0, -1):
            db.delete_all_except_last_n_records(i)
            assert len(db.get_all_records()) == i


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_get_record(name, columns, data_to_add):
    """
    Test removing all but last N records from table works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: int or str
    """
    with Database(name, columns) as db:
        for i in range(len(data_to_add)):
            db.add_data([i, data_to_add[i], int(False)])

        primary_column_name = [x.name for x in columns if x.primary][0]

        for primary_key_value in [2, 3]:
            entry = db.get_record(primary_key_value)
            assert entry[primary_column_name] == primary_key_value
            assert entry["state"] == data_to_add[primary_key_value]
            assert not entry["notified"]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_update_record(name, columns, data_to_add):
    with Database(name, columns) as db:
        for i in range(len(data_to_add)):
            db.add_data([i, data_to_add[i], int(False)])

        for primary_key_value in [2, 3]:
            entry = db.get_record(primary_key_value)
            assert not entry["notified"]
            db.update_record(primary_key_value, "notified", int(True))
            entry = db.get_record(primary_key_value)
            assert entry["notified"]
