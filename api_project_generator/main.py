import shutil
from datetime import date
from typing import Any, Callable, Optional, TypeVar, Union

import typer
from gyver.attrs import asdict
from gyver.database import Driver

from api_project_generator import commands
from api_project_generator.core.config import Config, get_config, set_config
from api_project_generator.core.user_data import GitData
from api_project_generator.helpers.utils import prettify
from api_project_generator.models import project_info
from api_project_generator.models.project_organization import ProjectOrganization
from api_project_generator.models.version import VersionType, validate_version_format

from .application import get_application

app = get_application()

T = TypeVar("T")

config = get_config()


def prompt_cast(
    prompt: str,
    default: Optional[T] = None,
    *,
    type_: Union[Callable[[Any], T], type[T]] = str,
) -> T:
    """
    Prompts the user with the given prompt message and casts the user input to the specified type.

    :param prompt: The prompt message shown to the user.
    :param default: Optional. The default value if the user provides no input.
    :param type_: The type to cast the user input to.
    :return: The casted user input.
    """
    return typer.prompt(prompt, default=default, type=type_)  # type: ignore


@app.command("create:api")
def create(
    db_driver: Optional[Driver] = typer.Option(
        None, help="The database driver to use."
    ),
    organization: ProjectOrganization = typer.Option(
        config.default_organization,
        help="The organization type of the project.",
    ),
    open_ide: Optional[str] = typer.Option(
        config.default_ide or None,
        help="The IDE to open after project creation.",
    ),
):
    """
    Command handler for creating an API project.

    :param db_driver: Optional. The database driver to use. Defaults to None.

    :param organization: Optional. The organization type of the project. Defaults to ProjectOrganization.STRUCTURAL.

    :param open_ide: Optional. The IDE to open after project creation. Defaults to None.
    """
    project_name = prompt_cast("Enter the project name")
    version_type = prompt_cast(
        "Enter the version format",
        config.default_version_type,
        type_=VersionType,
    )
    version = prompt_cast(
        "Enter the initial version of the project",
        "0.1.0"
        if version_type is VersionType.SEMVER
        else ".".join(date.today().isoformat().split("-")[:2]),
    )
    validate_version_format(version, version_type)

    description = prompt_cast("Enter the project description", "")

    git_data = GitData()
    fullname = prompt_cast("Enter your full name", git_data.default_fullname())
    email = prompt_cast("Enter your email", git_data.default_email())

    pyver = prompt_cast(
        "Enter the Python version",
        config.default_pyver,
    )

    info = project_info.ProjectInfo(
        config,
        project_name,
        version,
        version_type,
        description,
        fullname,
        email,
        db_driver,
        organization,
        pyver,
    )
    return commands.create_api(open_ide, info)


@app.command("cache:clear")
def clear_cache():
    """
    Clears the cache.
    """
    cache_dir = config.cache_dir
    shutil.rmtree(cache_dir)
    typer.echo(f"Cache cleared at: {cache_dir}")


@app.command("config:change")
def configure(
    pypi_url: Optional[str] = typer.Option(None, "--pypi-url"),
    gitignore_url: Optional[str] = typer.Option(None, "--gitignore-url"),
    default_ide: Optional[str] = typer.Option(None, "--default-ide"),
    default_cache_dir: Optional[str] = typer.Option(None, "--default-cache-dir"),
    default_docker_executable: Optional[str] = typer.Option(
        None, "--default-docker-executable"
    ),
    default_pyver: Optional[str] = typer.Option(None, "--default-pyver"),
    default_organization: Optional[ProjectOrganization] = typer.Option(
        None, "--default-organization"
    ),
    default_version_type: Optional[VersionType] = typer.Option(
        None, "--default-version-type"
    ),
):
    default_config = config
    opts = {}
    if pypi_url:
        opts["pypi_url"] = pypi_url
    if gitignore_url:
        opts["gitignore_url"] = gitignore_url
    if default_ide:
        opts["default_ide"] = default_ide
    if default_cache_dir:
        opts["default_cache_dir"] = default_cache_dir
    if default_docker_executable:
        opts["default_docker_executable"] = default_docker_executable
    if default_pyver:
        opts["default_pyver"] = default_pyver
    if default_organization:
        opts["default_organization"] = default_organization
    if default_version_type:
        opts["default_version_type"] = default_version_type
    set_config(Config(**asdict(default_config) | opts))


@app.command("config:show")
def show_config():
    """
    Show the current configuration.
    """
    config_dict = asdict(config)
    config_str = prettify(config_dict)
    typer.echo(config_str)


@app.command("create:table")
def create_table(table_module: str, table_name: str = typer.Argument("")):
    if not table_name:
        table_name = typer.prompt("Digite o nome da tabela")
    return commands.create_table(table_module, table_name)


@app.command("create:dto")
def create_dto(dto_module: str, dto_name: str = typer.Argument("")):
    if not dto_name:
        dto_name = typer.prompt("Digite o nome do DTO")
    return commands.create_dto(dto_module, dto_name)


@app.command("create:enum")
def create_enum(
    enum_name: str = typer.Argument(""), auto_opts: Optional[list[str]] = None
):
    if not enum_name:
        enum_name = typer.prompt("Digite o nome do enum")
    return commands.create_enum(enum_name, auto_opts)


@app.command("create:entity")
def create_entity(
    module: str,
    name: str = typer.Argument(""),
    sync: bool = typer.Option(False),
):
    if not name:
        name = typer.prompt("Digite o nome da entidade")
    return commands.create_entity(module, name, sync)


@app.command("update:imports")
def update_imports():
    return commands.update_imports()
