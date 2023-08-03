import re

from api_project_generator.core.cache import Cache
from api_project_generator.core.config import get_config

from .external import get_package_info

DEFAULT_API_DEPENDENCIES = {
    "fastapi",
    "uvicorn",
}
DEFAULT_DEV_DEPENDENCIES = {
    "pytest",
    "pylint",
    "black",
    "pytest-cov",
    "coverage",
    "pytest-asyncio",
    "sqlalchemy2-stubs",
    "faker",
}

DEFAULT_DEPLOY_DEPENDENCIES = {
    "httptools",
    "uvloop",
    "gunicorn",
    "circus",
}


def get_dependency_table(lib: str, version: str, *extras: str):
    version = f"^{version}"
    return (
        {lib: {"version": version, "extras": list(extras)}}
        if extras
        else {lib: version}
    )


def get_optional_dependency_table(lib: str, version: str, *extras: str):
    version = f"^{version}"
    table = {"version": version, "optional": True}
    if extras:
        table["extras"] = list(extras)
    return {lib: table}


extra_pattern = re.compile(r"\[(.+)\]")


def dependency_and_extras(lib: str):
    if match := extra_pattern.search(lib):
        extras = list(map(str.strip, match[1].split(",")))
        return lib.replace(f"[{match[1]}]", ""), extras
    return lib, []


def get_latest_version(lib: str):
    return get_package_info(lib, Cache(get_config().default_cache_dir))["info"][
        "version"
    ]


def get_dependency(lib: str, optional: bool = False):
    dep, extras = dependency_and_extras(lib)
    latest_version = get_latest_version(dep)
    if optional:
        return get_optional_dependency_table(dep, latest_version, *extras)
    return get_dependency_table(dep, latest_version, *extras)
