import re
from enum import Enum

import typer


class VersionType(str, Enum):
    SEMVER = "semver"
    CALVER = "calver"


SEMVER_REGEX = re.compile(r"^\d+\.\d+\.\d+$")
CALVER_REGEX = re.compile(r"^\d{4}\.\d{2}$")


def validate_version_format(version: str, version_type: VersionType):
    if version_type is VersionType.SEMVER:
        if SEMVER_REGEX.match(version) is None:
            raise typer.BadParameter(f"Invalid SEMVER format: {version}")
    elif version_type is VersionType.CALVER:
        if CALVER_REGEX.match(version) is None:
            raise typer.BadParameter(f"Invalid CALVER format: {version}")
    else:
        raise typer.BadParameter("Invalid version type")
