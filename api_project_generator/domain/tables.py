import os
from pathlib import Path
from typing import Optional

from api_project_generator.files import Files
from api_project_generator.functions import clean_name, to_snake
from api_project_generator.services import strings


def _find_directory(path: Path, dir_name: str) -> Optional[Path]:
    for item in path.glob("**{}".format(os.sep)):
        if item.name == "tables":
            return item
    return None


def find_tables_directory(path: Path):
    return _find_directory(path, "tables")


def find_metadata(curdir: Path) -> Optional[Path]:
    tables_dir = find_tables_directory(curdir)
    if not tables_dir:
        return None
    metadata = tables_dir.parent / Files.python_file("metadata")
    if metadata.exists():
        return metadata
    return None


def prepare_table_python_name(table_name: str):
    return to_snake(clean_name(table_name))


def create_table_file(
    tables_dir: Path, table_module: str, table_name: str
) -> Optional[tuple[Path, Path]]:
    table_module_dir = tables_dir / table_module
    dunder_file = table_module_dir / Files.python_file("__init__")
    if not table_module_dir.exists():
        table_module_dir.mkdir()
        dunder_file.touch()
    if table_module_dir.is_file():
        return None
    table_file = table_module_dir / Files.python_file(
        prepare_table_python_name(table_name)
    )
    if table_file.exists():
        return None
    table_file.touch()
    return table_file, dunder_file


def write_table_file(file: Path, project_folder: Path, table_name: str):
    with file.open("w") as stream:
        stream.write(
            strings.TABLE_TEMPLATE.format(
                project_folder=project_folder.name,
                table_normalized_name=prepare_table_python_name(table_name),
                table_name=table_name,
            )
        )


def update_dunder_file(dunder_file: Path):
    table_dir = dunder_file.parent
    files = [
        file
        for file in table_dir.glob("*")
        if file.name != Files.python_file("__init__") and file.is_file()
    ]
    imports = "\n".join(
        strings.TABLES_DUNDER_IMPORT_TEMPLATE.format(
            table_file=file.name.removesuffix(".py")
        )
        for file in files
    )
    tables = ",".join('"{}"'.format(file.name.removesuffix(".py")) for file in files)
    with dunder_file.open("w") as stream:
        stream.write(
            strings.TABLES_DUNDER_TEMPLATE.format(imports=imports, tables=tables)
        )
