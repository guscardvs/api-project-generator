import importlib
import inspect
from pathlib import Path
from typing import Optional

from sqlalchemy import Table


class ModelFinder:
    def __init__(self, path: Path, root: Path = None):
        self.path = path
        self.models = {{}}
        self.root = root or path

    def find(self):
        if self.path.is_dir():
            self.find_from_dir()
        else:
            self.find_from_file()

    def find_from_dir(self, path: Optional[Path] = None):
        if path is None:
            path = self.path
        if "pycache" in path.name or ".pyc" in path.name:
            return
        for item in path.iterdir():
            if item.is_dir():
                self.find_from_dir(item)
                continue
            if ".py" in path.name and "__init__.py" != path.name:
                continue
            self.find_from_file(item)

    def find_from_file(self, path: Optional[Path] = None):
        if path is None:
            path = self.path
        if not path.is_file():
            return
        mod = importlib.import_module(self.get_import(path))
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj):
                if issubclass(obj, Table) and name != "Table":
                    self.models[name] = obj

    def get_import(self, target: Path):
        target_str = str(target)
        result = target_str[target_str.index(self.root.name):].replace("/", ".").replace(".py", "")
        return result

    def __getitem__(self, name: str) -> Table:
        if self.models.get(name):
            return self.models[name]
        raise KeyError(name)


