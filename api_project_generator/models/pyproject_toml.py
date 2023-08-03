import re
from typing import Any, Callable

import tomlkit
from gyver.attrs import define, info
from gyver.database import Driver

from api_project_generator.core import dependencies, user_data
from api_project_generator.models.project_info import ProjectInfo


@define
class PyprojectToml:
    project_info: ProjectInfo
    dependencies: set[str] = info(default_factory=set)
    dev_dependencies: set[str] = info(default_factory=set)
    optional_dependencies: set[str] = info(default_factory=set)

    def __post_init__(self):
        if self.project_info.driver is None:
            self.dependencies.add("gyver")
        elif self.project_info.driver is Driver.POSTGRES:
            self.dependencies.add("gyver[db-pg]")
        elif self.project_info.driver is Driver.CUSTOM:
            self.dependencies.update({"gyver", "sqlalchemy"})
        else:
            self.dependencies.add(f"gyver[db-{self.project_info.driver.value}]")

    def get_dependencies(self, *, parser: Callable[[str], dict[str, Any]]):
        dependencies = {"python": f"^{self.project_info.effective_pyver}"}
        for item in self.dependencies.union(self.optional_dependencies):
            dependencies |= parser(item)
        return dependencies

    def get_dev_dependencies(self, *, parser: Callable[[str], dict[str, Any]]):
        dependencies = {}
        for item in self.dev_dependencies:
            dependencies |= parser(item)
        return dependencies

    def get_project_title(self):
        string = self.project_info.name.replace("-", " ").replace("_", " ")
        string = re.sub(
            "([a-z])([A-Z])", lambda match: f"{match[1]} {match[2]}", string
        )
        return string.title()

    def dependency_parse(self, dependency_dict: dict[str, Any]):
        out = {}
        for key, value in dependency_dict.items():
            if isinstance(value, str):
                out[key] = value
            else:
                table = tomlkit.inline_table()
                table.update(value)
                out[key] = table
        return out

    def make_table(self, project_folder: str):
        return {
            "tool": {
                "poetry": {
                    "name": self.project_info.name,
                    "version": self.project_info.version,
                    "description": self.project_info.description,
                    "authors": [
                        user_data.get_user_signature(
                            self.project_info.fullname,
                            self.project_info.email,
                        )
                    ],
                    "dependencies": self.dependency_parse(
                        self.get_dependencies(parser=dependencies.get_dependency)
                    ),
                    "group": {
                        "dev": {
                            "dependencies": self.dependency_parse(
                                self.get_dev_dependencies(
                                    parser=dependencies.get_dependency
                                )
                            )
                        }
                    },
                    "scripts": {"start": f"{project_folder}.main:main"},
                    "extras": {"deploy": list(self.optional_dependencies)},
                }
            },
            "build-system": {
                "requires": ["poetry-core>=1.0.0"],
                "build-backend": "poetry.core.masonry.api",
            },
        }
