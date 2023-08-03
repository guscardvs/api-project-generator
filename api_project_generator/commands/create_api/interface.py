import pathlib
from typing import Protocol

from gyver.filetree import FileTree

from api_project_generator import models


class ApiGenerator(Protocol):
    def __init__(
        self,
        base_dir: pathlib.Path,
        files: FileTree,
        pyproject_toml: models.PyprojectToml,
    ) -> None:
        ...

    def create(self) -> None:
        ...
