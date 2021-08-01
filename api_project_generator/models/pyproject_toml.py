from api_project_generator.models.project_info import DbType
import re
from dataclasses import dataclass, field
from typing import Callable

from api_project_generator.helpers.functions import get_python_version


@dataclass
class PyprojectToml:
    project_name: str
    version: str
    description: str = ""
    fullname: str = ""
    email: str = ""
    _dependencies: set[str] = field(default_factory=set)
    _dev_dependencies: set[str] = field(default_factory=set)
    _optional_dependencies: set[str] = field(default_factory=set)
    db_type: DbType = DbType.MYSQL

    def __post_init__(self):
        if self.db_type == DbType.POSTGRES:
            self._dependencies.remove("aiomysql")
        else:
            self._dependencies.remove("asyncpg")
            self._dependencies.remove("psycopg2-binary")
            self._optional_dependencies.remove("psycopg2")

    @property
    def dependencies(self):
        return list(self._dependencies)

    @dependencies.setter
    def dependencies(self, string: str):
        self._dependencies.add(string)

    @property
    def dev_dependencies(self):
        return list(self._dev_dependencies)

    @dev_dependencies.setter
    def dev_dependencies(self, string: str):
        self._dev_dependencies.add(string)
    
    @property
    def optional_dependencies(self):
        return list(self._optional_dependencies)

    @optional_dependencies.setter
    def optional_dependencies(self, string: str):
        self._optional_dependencies.add(string)
    
    

    def get_dependencies(self, *, dev: bool, parser: Callable[[str], str]):
        deps = self.dependencies if not dev else self.dev_dependencies
        res = "\n".join(parser(item) for item in deps) 
        return (f"{get_python_version()}\n" + res) if not dev else res

    def get_optional_dependencies(self, parser: Callable[[str], str]):
        return "\n" + "\n".join(parser(item) for item in self._optional_dependencies)

    def get_project_title(self):
        string = self.project_name.replace("-", " ").replace("_", " ")
        string = re.sub("([a-z])([A-Z])", lambda match: f"{match[1]} {match[2]}", string)
        return string.title()