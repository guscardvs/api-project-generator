from pathlib import Path

from api_project_generator.functions import (
    clean_name,
    find_directory,
    to_camel,
    to_snake,
)
from api_project_generator.services import strings


def find_dtos_dir(path: Path):
    return find_directory(path, "dtos")


def write_dto_file(dto_file: Path, project_folder: Path, dto_name: str):
    with dto_file.open("w") as stream:
        stream.write(
            strings.DTO_TEMPLATE.format(
                project_folder=project_folder.name,
                dto_name=to_camel(to_snake(clean_name(dto_name))),
            )
        )