import json
from typing import List


class DatabaseKeys:
    from library.config import PubSubKeys
    STATE = PubSubKeys.STATE
    ID = PubSubKeys.ID
    TIMESTAMP = "timestamp"
    CAPTURED = "captured"
    TOGGLED = "toggled"
    NOTIFIED = "notified"


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
        """
        Convenience object to house a single database row
        @param columns: List of columns in the database
        @param entry: raw entry from SQL query
        @type entry:
        """
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

    def get(self, item: str, default_val=None) -> int or float or str:
        return self.values.get(item, default_val)

    def __getitem__(self, item) -> int or float or str:
        return self.values.get(item)

    def __repr__(self) -> str:
        return json.dumps(self._values)
