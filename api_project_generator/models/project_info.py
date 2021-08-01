from dataclasses import dataclass
from enum import Enum


@dataclass
class ProjectInfo:
    name: str
    version: str
    description: str
    fullname: str
    email: str
    db_type: str


class DbType(str, Enum):
    MYSQL = "mysql"
    POSTGRES = "postgres"
