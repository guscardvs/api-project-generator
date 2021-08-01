from dataclasses import dataclass
from enum import Enum


@dataclass
class ProjectInfo:
    name: str
    version: str
    description: str
    fullname: str
    email: str
    db_type: "DbType"


class DbType(str, Enum):
    MYSQL = "mysql"
    POSTGRES = "postgres"

    def get_db_port(self):
        _options = {
            DbType.POSTGRES: 5432,
            DbType.MYSQL: 3306
        }
        return _options[self]