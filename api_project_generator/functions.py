import builtins
import os
import re
import sys
from pathlib import Path

from git import GitConfigParser
from api_project_generator.services.repository import pypi_repository


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
