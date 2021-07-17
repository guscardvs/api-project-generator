import os
import re
import sys
from pathlib import Path
from typing import Callable, Optional
from unicodedata import normalize

from git import GitConfigParser
import typer

from api_project_generator.files import Files
from api_project_generator.services.repository import pypi_repository
from api_project_generator.services import strings


def get_curdir():
    return Path.cwd()


def get_default_fullname() -> str:
    reader = GitConfigParser()
    return reader.get_value("user", "name", "")  # type: ignore


def get_default_email() -> str:
    reader = GitConfigParser()
    return reader.get_value("user", "email", "")  # type: ignore


def get_user_signature(fullname: str, email: str):
    return "{name} <{email}>".format(name=fullname, email=email)


def get_latest_version(lib: str):
    return pypi_repository.get_package_info(lib)["info"]["version"]


def _get_dependency_string(lib: str, version: str, extra: str = None):
    if extra:
        return f'{lib} = {{ extras = ["{extra}"], version= "^{version}" }}'
    return f'{lib} = "^{version}"'


def get_optional_dependency_string(lib: str, version: str):
    return f'{lib} = {{ version= "^{version}", optional = true }}'


def dependency_and_extra(lib: str):
    if match := re.search(r"\[([a-zA-Z]+)\]", lib):
        return lib.replace(f"[{match[1]}]", ""), match[1]
    return lib, ""


def get_dependency_string(lib: str, optional: bool = False):
    if optional:
        return get_optional_dependency_string(lib, get_latest_version(lib))
    dep, extra = dependency_and_extra(lib)
    return _get_dependency_string(dep, get_latest_version(dep), extra)


def get_python_version():
    return f'python = "^{sys.version_info.major}.{sys.version_info.minor}"'


def to_snake(name: str):
    return re.sub(
        "([a-z])([A-Z])", lambda match: f"{match[1]}_{match[2]}".lower(), name
    )


def clean_name(string: str):
    return normalize("NFC", string.strip().replace("-", "_").lower())


def find_directory(path: Path, dir_name: str) -> Optional[Path]:
    for item in path.glob("**{}".format(os.sep)):
        if item.name == dir_name:
            return item
    return None


def to_camel(string: str):
    return "".join(item.title() for item in string.split("_"))


def _default_public_name_parser(string: str):
    return string.removeprefix("_").removesuffix(".py")


def camel_public_name_parser(string: str) -> str:
    return to_camel(to_snake(clean_name(string.removeprefix("_").removesuffix(".py"))))


def update_dunder_file(
    dunder_file: Path, public_name_parser: Callable[[str], str] = None
):
    dir = dunder_file.parent
    files = [
        file
        for file in dir.glob("*")
        if file.name != Files.python_file("init", dunder=True) and file.is_file()
    ]
    public_name_parser = public_name_parser or _default_public_name_parser
    imports = "\n".join(
        strings.DUNDER_IMPORT_TEMPLATE.format(
            file=file.name.removesuffix(".py"),
            public_name=public_name_parser(file.name),
        )
        for file in files
    )
    classes = ",".join('"{}"'.format(public_name_parser(file.name)) for file in files)
    with dunder_file.open("w") as stream:
        stream.write(strings.DUNDER_TEMPLATE.format(imports=imports, classes=classes))
