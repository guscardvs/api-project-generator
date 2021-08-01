from pathlib import Path


class Files:
    def __init__(self, base_dir: Path) -> None:
        self._files = {"_dir": base_dir}
        if not base_dir.exists():
            base_dir.mkdir()

    @property
    def base_dir(self):
        return self._files["_dir"]

    def create_path_dict(self, *path: str):
        for idx, item in enumerate(path):
            if not isinstance(self._files.get("dirname"), dict):
                self._files[item] = {"_dir": self.get_base_dir(*path[:idx]) / item}  # type: ignore

    def get_base_dir(self, *path: str) -> Path:
        base_dir = self.base_dir
        for item in path:
            base_dir /= item
        return base_dir

    def get_dir_dict(self, *path: str) -> dict:
        dir_dict = {}
        for item in path:
            dir_dict = self._files[item]
        return dir_dict  # type: ignore

    def create_dir(self, dirname: str, *path: str):
        if dirname == "_dir":
            dirname = "__dir"
        self.create_path_dict(*path)
        base_dir = self.get_base_dir(*path)
        dir = base_dir / dirname
        if not dir.exists():
            dir.mkdir()
        dir_dict = self.get_dir_dict(*path)
        dir_dict[dirname] = {"_dir": dir}

        return dir

    def create_file(self, filename: str, *path: str):
        if filename == "_dir":
            filename = "__dir"
        self.create_path_dict(*path)
        base_dir = self.get_base_dir(*path)
        file = base_dir / filename
        if not file.exists():
            file.touch()
        dir_dict = self.get_dir_dict(*path)
        dir_dict[filename] = file

        return file

    def get_file(self, filename: str, *path: str) -> Path:
        return self.get_dir_dict(*path)[filename]

    def get_dir(self, dirname: str, *path) -> Path:
        return self.get_dir_dict(*path)[dirname]["_dir"]

    @staticmethod
    def python_file(filename: str, *, private: bool = False, dunder: bool = False):
        response = filename
        if private:
            response= f"_{filename}"
        if dunder:
            response= f"__{filename}__"
        return f"{response}.py"
