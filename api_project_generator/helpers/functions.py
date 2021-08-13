from enum import Enum
import importlib
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional
from unicodedata import normalize

from git import GitConfigParser

from .repository import pypi_repository

from . import strings
from .files import Files
from .module_helper import ModuleMapper


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


def update_module_dunder_file(
    dunder_file: Path,
    project_folder: Path,
    inheritance_finder: Callable[[str], tuple[bool, type[Any]]],
):

    """update_module_dunder_file updates imports on dunder file. inheritance finder must be a callable which receives project_folder_name and returns a tuple with is_class(bool) and parent(type).
    if is_class is true will compare via issubclass else will use isinstance"""

    is_class, parent = inheritance_finder(project_folder.name)
    if is_class:
        module_mapper = ModuleMapper(
            dunder_file.parent, project_folder, child_of=parent
        )
    else:
        module_mapper = ModuleMapper(
            dunder_file.parent, project_folder, instance_of=parent
        )
    module_mapper.find()
    findings = module_mapper.get_findings()
    with dunder_file.open("w") as stream:
        stream.write(
            strings.DUNDER_TEMPLATE.format(
                imports="\n".join(findings.generate_import_string()),
                classes=",".join(
                    '"{}"'.format(item)
                    for item in findings.all_keys()
                ),
            )
        )


def get_env_location():
    result = subprocess.run(["poetry", "show", "-v"], capture_output=True)
    try:
        result= result.stdout.decode().split("\n")[0].split()[-1]
    except IndexError:
        raise ImportError
    else:
        return Path(result) / "lib" / "python3.9" / "site-packages", Path(result) / "lib64" / "python3.9" / "site-packages"

def prepare_to_import(project_folder: Path):
    env_paths = get_env_location()
    for item in env_paths:
        if item.exists():
            sys.path.append(str(item))
    sys.path.append(str(project_folder.parent))

def reload_import(project_folder: Path):
    sys.path.remove(str(project_folder.parent))
    sys.path.append(str(project_folder.parent))


def dto_inheritance_finder(project_folder: str) -> tuple[bool, type]:
    return True, getattr(importlib.import_module(f"{project_folder}.dtos.base"), "DTO")


def enum_inheritance_finder(_: str):
    return True, Enum


def table_inheritance_finder(_: str):
    from sqlalchemy import Table  # type: ignore

    return False, Table


def repo_inheritance_finder(project_folder: str):
    return True, getattr(
        importlib.import_module(f"{project_folder}.database.helpers"),
        "Repository",
        object,
    )


def routes_inheritance_finder(_: str):
    from fastapi import APIRouter  # type: ignore

    return False, APIRouter


def open_in_code(name: str):
    if "win" not in sys.platform.lower():
        args = ["code", name]
    else:
        args = ["code.cmd", name]
    try:
        subprocess.run(args)
    except FileNotFoundError:
        try:
            args = ["code-insiders", name]
            subprocess.run(args)
        except FileNotFoundError:
            return False
    return True
