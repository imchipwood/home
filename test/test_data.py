import os
from typing import List

import pytest

from library.data import Column
from library.data.database import Database, get_database_path

DB_PATH = get_database_path("TEST_DB")

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


def arrange_data_for_insert(data_to_add: List[int or str]) -> List[tuple]:
    num_rows = len(data_to_add)
    data = [x for x in zip(range(num_rows), data_to_add, [int(False) for x in range(num_rows)])]
    return data


def remove_dbs():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def setup_function():
    remove_dbs()


def teardown_module():
    remove_dbs()


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
    with Database(name, columns, DB_PATH) as db:
        assert os.path.exists(DB_PATH)
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
    with Database(name, columns, DB_PATH) as db:
        db.add_data([0, data_to_add, int(False)])

        assert len(db.get_all_records()) == 1


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 1, 0, 1, 0]),
    (DB1_NAME, DB1_COLUMNS, ["Hi", "There", "You"])
])
def test_add_data_multiple(name: str, columns: List[Column], data_to_add: int or str):
    """
    Test adding multiple entries to a table at once works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, columns, DB_PATH) as db:
        data = arrange_data_for_insert(data_to_add)
        db.add_data_multiple(data)

        assert len(db.get_all_records()) == len(data_to_add)


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
    @type data_to_add: list[int or str]
    """
    with Database(name, columns, DB_PATH) as db:
        data = arrange_data_for_insert(data_to_add)
        db.add_data_multiple(data)

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
    @type data_to_add: list[int or str]
    """
    with Database(name, columns, DB_PATH) as db:
        data = arrange_data_for_insert(data_to_add)
        db.add_data_multiple(data)

        latest = db.get_latest_record()
        assert latest[columns[0].name] == 4
        assert latest[columns[1].name] == data_to_add[-1]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "c", "e"])
])
def test_delete_all_except_last_n_records(name, columns, data_to_add):
    """
    Test removing all but last N records from table works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, columns, DB_PATH) as db:
        data = arrange_data_for_insert(data_to_add)
        db.add_data_multiple(data)

        for i in range(len(data_to_add), 0, -1):
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
    @type data_to_add: list[int or str]
    """
    with Database(name, columns, DB_PATH) as db:
        data = arrange_data_for_insert(data_to_add)
        db.add_data_multiple(data)

        primary_column_name = [x.name for x in columns if x.primary][0]

        for primary_key_value in [2, 3]:
            entry = db.get_record(primary_key_value)
            assert entry[primary_column_name] == primary_key_value
            assert entry["state"] == data_to_add[primary_key_value]
            assert not entry["notified"]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c"])
])
def test_update_record(name, columns, data_to_add):
    """
    Test updating a record works
    @param name: name of table
    @type name: str
    @param columns: list of columns to add to table
    @type columns: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, columns, DB_PATH) as db:
        data = arrange_data_for_insert(data_to_add)
        db.add_data_multiple(data)

        for primary_key_value in [2]:
            entry = db.get_record(primary_key_value)
            assert not entry["notified"]
            db.update_record(primary_key_value, "notified", int(True))
            entry = db.get_record(primary_key_value)
            assert entry["notified"]
