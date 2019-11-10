import os

from library.data.database import Column, Database, get_database_path

DB_NAME = "PITEST_DB"
DB_COLUMNS = [
    Column("timestamp", "integer", "PRIMARY KEY"),
    Column("state", "integer", "NOT NULL")
]


def remove_db():
    db_path = get_database_path(DB_NAME)
    if os.path.exists(db_path):
        os.remove(db_path)


def setup_module():
    remove_db()


def teardown_function():
    remove_db()


def teardown_module():
    remove_db()


def test_create_database():
    with Database(DB_NAME, DB_COLUMNS) as db:
        assert os.path.exists(get_database_path(DB_NAME))


def test_add_to_database():
    with Database(DB_NAME, DB_COLUMNS) as db:
        db.add_data([0, 0])
        db.add_data([1, 0])
        db.add_data([2, 0])

        assert len(db.get_all_records()) == 3


def test_get_last_n_records():
    with Database(DB_NAME, DB_COLUMNS) as db:
        db.add_data([0, 0])
        db.add_data([1, 0])
        db.add_data([2, 0])
        db.add_data([3, 1])
        db.add_data([4, 1])

        assert len(db.get_last_n_records(1)) == 1
        assert len(db.get_last_n_records(2)) == 2
        last_3 = db.get_last_n_records(3)
        assert last_3[0][0] == 4
        assert last_3[0][1] == 1
        assert last_3[1][0] == 3
        assert last_3[1][1] == 1
        assert last_3[2][0] == 2
        assert last_3[2][1] == 0


def test_get_latest_record():
    with Database(DB_NAME, DB_COLUMNS) as db:
        db.add_data([0, 0])
        db.add_data([1, 0])
        db.add_data([2, 0])
        db.add_data([3, 1])
        db.add_data([4, 1])

        latest = db.get_latest_record()
        assert latest[0] == 4
        assert latest[1] == 1
