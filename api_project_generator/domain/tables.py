import os
from pathlib import Path
from typing import Optional

from api_project_generator.files import Files
from api_project_generator.functions import (
    clean_name,
    find_directory,
    to_snake,
)
from api_project_generator.services import strings


def find_tables_directory(path: Path):
    return find_directory(path, "tables")


def find_metadata(curdir: Path) -> Optional[Path]:
    tables_dir = find_tables_directory(curdir)
    if not tables_dir:
        return None
    metadata = tables_dir.parent / Files.python_file("metadata")
    if metadata.exists():
        return metadata
    return None


def write_table_file(file: Path, project_folder: Path, table_name: str):
    with file.open("w") as stream:
        stream.write(
            strings.TABLE_TEMPLATE.format(
                project_folder=project_folder.name,
                table_normalized_name=to_snake(clean_name(table_name)),
                table_name=table_name,
            )
        )
