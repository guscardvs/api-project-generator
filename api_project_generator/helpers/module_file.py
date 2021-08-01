from pathlib import Path

import typer

from .files import Files
from .functions import clean_name, to_snake


class ModuleFile:
    def __init__(self, parent_dir: Path, module: str, filename: str) -> None:
        self.parent_dir = parent_dir
        self.module = module
        self.filename = filename

    def create(self):
        module_dir = self.parent_dir / self.module
        dunder_file = module_dir / Files.python_file("init", dunder=True)
        if not module_dir.exists():
            module_dir.mkdir()
            dunder_file.touch()
        if module_dir.is_file():
            return None
        file = module_dir / Files.python_file(
            to_snake(clean_name(self.filename)), private=True
        )
        if file.exists():
            return None
        file.touch()
        return file, dunder_file

    def retrieve_or_exit(self):
        response = self.create()
        if not response:
            typer.echo("Módulo é um arquivo e não um diretório ou Arquivo já existe")
            raise typer.Exit()
        return response