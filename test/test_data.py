import os
from typing import List, Dict

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
TABLE0 = {
    DB0_NAME: DB0_COLUMNS
}
TABLE1 = {
    DB1_NAME: DB1_COLUMNS
}


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


@pytest.mark.parametrize("name,table_dict", [
    (DB0_NAME, TABLE0),
    (DB1_NAME, TABLE1)
])
def test_create_table(name: str, table_dict: Dict[str, List[Column]]):
    """
    Test creating table works
    @param name: name of table
    @type name: str
    @param table_dict: list of columns to add to table
    @type table_dict: list[Column]
    """
    with Database(name, table_dict, DB_PATH) as db:
        assert os.path.exists(DB_PATH)
        table = db.get_table(name)
        assert table.does_table_exist(name)


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, 0),
    (DB1_NAME, TABLE1, "hello")
])
def test_add_to_table(name: str, table_dict: Dict[str, List[Column]], data_to_add: int or str):
    """
    Test adding info to tables work
    @param name: name of table
    @type name: str
    @param table_dict: Dict of list of columns to add to table
    @type table_dict: Dict[str, List[Column]]
    @param data_to_add: data to add to table
    @type data_to_add: int or str
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        table.add_data([0, data_to_add, int(False)])

        assert len(table.get_all_records()) == 1


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, [0, 1, 0, 1, 0]),
    (DB1_NAME, TABLE1, ["Hi", "There", "You"])
])
def test_add_data_multiple(name: str, table_dict: Dict[str, List[Column]], data_to_add: int or str):
    """
    Test adding multiple entries to a table at once works
    @param name: name of table
    @type name: str
    @param table_dict: list of columns to add to table
    @type table_dict: List[Column]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        data = arrange_data_for_insert(data_to_add)
        table.add_data_multiple(data)

        assert len(table.get_all_records()) == len(data_to_add)


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, [0, 0, 0, 1, 1]),
    (DB1_NAME, TABLE1, ["a", "b", "c", "d", "e"])
])
def test_get_last_n_records(name, table_dict, data_to_add):
    """
    Test getting last n records from table works
    @param name: name of table
    @type name: str
    @param table_dict: list of columns to add to table
    @type table_dict: Dict[str, List[Column]]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        data = arrange_data_for_insert(data_to_add)
        table.add_data_multiple(data)

        columns = table.columns
        assert len(table.get_last_n_records(1)) == 1
        assert len(table.get_last_n_records(2)) == 2
        last_3 = table.get_last_n_records(3)
        assert last_3[0][columns[0].name] == 4
        assert last_3[0][columns[1].name] == data_to_add[-1]
        assert last_3[1][columns[0].name] == 3
        assert last_3[1][columns[1].name] == data_to_add[-2]
        assert last_3[2][columns[0].name] == 2
        assert last_3[2][columns[1].name] == data_to_add[-3]


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, [0, 0, 0, 1, 1]),
    (DB1_NAME, TABLE1, ["a", "b", "c", "d", "e"])
])
def test_get_latest_record(name, table_dict, data_to_add):
    """
    Test getting latest table record works
    @param name: name of table
    @type name: str
    @param table_dict: list of columns to add to table
    @type table_dict: Dict[str, List[Column]]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        data = arrange_data_for_insert(data_to_add)
        table.add_data_multiple(data)

        columns = table.columns
        latest = table.get_latest_record()
        assert latest[columns[0].name] == 4
        assert latest[columns[1].name] == data_to_add[-1]


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, [0, 1, 1]),
    (DB1_NAME, TABLE1, ["a", "c", "e"])
])
def test_delete_all_except_last_n_records(name, table_dict, data_to_add):
    """
    Test removing all but last N records from table works
    @param name: name of table
    @type name: str
    @param table_dict: dict of columns to add to table
    @type table_dict: Dict[str, List[Column]]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        data = arrange_data_for_insert(data_to_add)
        table.add_data_multiple(data)

        for i in range(len(data_to_add), 0, -1):
            table.delete_all_except_last_n_records(i)
            assert len(table.get_all_records()) == i


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, [0, 0, 0, 1, 1]),
    (DB1_NAME, TABLE1, ["a", "b", "c", "d", "e"])
])
def test_get_record(name, table_dict, data_to_add):
    """
    Test removing all but last N records from table works
    @param name: name of table
    @type name: str
    @param table_dict: list of columns to add to table
    @type table_dict: Dict[str, List[Column]]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        data = arrange_data_for_insert(data_to_add)
        table.add_data_multiple(data)

        primary_column_name = [x.name for x in table.columns if x.primary][0]

        for primary_key_value in [2, 3]:
            entry = table.get_record(primary_key_value)
            assert entry[primary_column_name] == primary_key_value
            assert entry["state"] == data_to_add[primary_key_value]
            assert not entry["notified"]


@pytest.mark.parametrize("name,table_dict,data_to_add", [
    (DB0_NAME, TABLE0, [0, 0, 0]),
    (DB1_NAME, TABLE1, ["a", "b", "c"])
])
def test_update_record(name, table_dict, data_to_add):
    """
    Test updating a record works
    @param name: name of table
    @type name: str
    @param table_dict: list of columns to add to table
    @type table_dict: Dict[str, List[Column]]
    @param data_to_add: data to add to table
    @type data_to_add: list[int or str]
    """
    with Database(name, table_dict, DB_PATH) as db:
        table = db.get_table(name)
        data = arrange_data_for_insert(data_to_add)
        table.add_data_multiple(data)

        for primary_key_value in [2]:
            entry = table.get_record(primary_key_value)
            assert not entry["notified"]
            table.update_record(primary_key_value, "notified", int(True))
            entry = table.get_record(primary_key_value)
            assert entry["notified"]
