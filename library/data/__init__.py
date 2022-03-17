import json
from typing import List


class Column:
    def __init__(self, col_name: str, col_type: str, col_key: str, foreign_table: str = None):
        """
        Initialize a database column object
        @param col_name: name of column
        @type col_name: str
        @param col_type: data type of column
        @type col_type: str
        @param col_key: column key type
        @type col_key: str
        @param foreign_table: optional related table - column name must be identical
        @type foreign_table: str
        """
        super()
        self.name = col_name
        self.type = col_type
        self.key = col_key
        self.foreign_table = foreign_table

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

    def get_table_reference(self) -> str:
        """
        Get the database table creation string for referencing another table
        @return: string representation of table reference
        @rtype: str
        """
        if self.foreign_table:
            return f", FOREIGN KEY({self.name}) REFERENCES {self.foreign_table}({self.name})"
        return ""


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
