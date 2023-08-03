import shutil
from pathlib import Path
from typing import Optional

from gyver.database import DatabaseConfig, Driver
from gyver.database.drivers.utils import resolve_driver

from api_project_generator.helpers.utils import find_next_available_port

DEFAULT_LOCALUSER = "localuser"
DEFAULT_LOCALPASSWORD = "localPa5$word"


def make_local_db(driver: Driver, project_src: Path, project_name: str):
    if driver is Driver.SQLITE:
        return DatabaseConfig(
            driver,
            host=(project_src / f"{project_name}-localdb.sqlite3").as_posix(),
        )
    dialect = resolve_driver(driver)
    port = find_next_available_port(dialect.default_port)
    return DatabaseConfig(
        driver,
        "localhost",
        port,
        DEFAULT_LOCALUSER,
        DEFAULT_LOCALPASSWORD,
        name=f"{project_name}-localdb",
    )


def find_docker_executable(docker_executable: Optional[str] = None):
    opts = ["docker", "podman"]
    if docker_executable:
        opts.insert(0, docker_executable)
    if result := next((item for item in opts if shutil.which(item)), None):
        return result
    raise ValueError("No executable found for containers")
