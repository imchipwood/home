import os
import pytest

from library.data.database import Column, Database, get_database_path

DB0_NAME = "PITEST_DB0"
DB1_NAME = "PITEST_DB1"
DB0_COLUMNS = [
    Column("timestamp", "integer", "PRIMARY KEY"),
    Column("state", "integer", "NOT NULL")
]
DB1_COLUMNS = [
    Column("timestamp", "integer", "PRIMARY KEY"),
    Column("state", "string", "NOT NULL")
]


def remove_db():
    for db_name in [DB0_NAME, DB1_NAME]:
        db_path = get_database_path(db_name)
        if os.path.exists(db_path):
            os.remove(db_path)


def setup_module():
    remove_db()


def teardown_function():
    remove_db()


def teardown_module():
    remove_db()


@pytest.mark.parametrize("name,columns", [
    (DB0_NAME, DB0_COLUMNS),
    (DB1_NAME, DB1_COLUMNS)
])
def test_create_database(name, columns):
    with Database(name, columns) as db:
        assert os.path.exists(get_database_path(name))


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, 0),
    (DB1_NAME, DB1_COLUMNS, "hello")
])
def test_add_to_database(name, columns, data_to_add):
    with Database(name, columns) as db:
        db.add_data([0, data_to_add])
        db.add_data([1, data_to_add])
        db.add_data([2, data_to_add])

        assert len(db.get_all_records()) == 3


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_get_last_n_records(name, columns, data_to_add):
    with Database(name, columns) as db:
        for i in range(5):
            db.add_data([i, data_to_add[i]])

        assert len(db.get_last_n_records(1)) == 1
        assert len(db.get_last_n_records(2)) == 2
        last_3 = db.get_last_n_records(3)
        assert last_3[0][0] == 4
        assert last_3[0][1] == data_to_add[-1]
        assert last_3[1][0] == 3
        assert last_3[1][1] == data_to_add[-2]
        assert last_3[2][0] == 2
        assert last_3[2][1] == data_to_add[-3]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_get_latest_record(name, columns, data_to_add):
    with Database(name, columns) as db:
        for i in range(5):
            db.add_data([i, data_to_add[i]])

        latest = db.get_latest_record()
        assert latest[0] == 4
        assert latest[1] == data_to_add[-1]


@pytest.mark.parametrize("name,columns,data_to_add", [
    (DB0_NAME, DB0_COLUMNS, [0, 0, 0, 1, 1]),
    (DB1_NAME, DB1_COLUMNS, ["a", "b", "c", "d", "e"])
])
def test_delete_all_except_last_n_records(name, columns, data_to_add):
    with Database(name, columns) as db:
        for i in range(5):
            db.add_data([i, data_to_add[i]])

        db.delete_all_except_last_n_records(2)
        assert len(db.get_all_records()) == 2
