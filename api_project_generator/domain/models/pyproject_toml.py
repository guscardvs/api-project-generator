from dataclasses import dataclass, field
from typing import Callable

from api_project_generator.functions import get_python_version


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

    def get_dependencies(self, *, dev: bool, parser: Callable[[str], str]):
        deps = self.dependencies if not dev else self.dev_dependencies
        return f"{get_python_version()}\n" + "\n".join(parser(item) for item in deps)

    def get_optional_dependencies(self, parser: Callable[[str], str]):
        return "\n" + "\n".join(parser(item) for item in self._optional_dependencies)
