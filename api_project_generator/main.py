from api_project_generator.domain.enums import write_enum_file
import subprocess
import sys
from typing import Optional

import typer

from api_project_generator.domain.dtos import find_dtos_dir, write_dto_file
from api_project_generator.domain.git_repo import init_repository
from api_project_generator.domain.models.pyproject_toml import PyprojectToml
from api_project_generator.domain.structure import Structure
from api_project_generator.domain.tables import (
    find_metadata,
    find_tables_directory,
    write_table_file,
)
from api_project_generator.functions import (
    camel_public_name_parser,
    get_curdir,
    get_default_email,
    get_default_fullname,
    update_dunder_file,
)
from api_project_generator.module_file import ModuleFile

from .application import get_application

app = get_application()


@app.command()
def create(code: bool = typer.Option(False)):
    project_name = typer.prompt("Digite o nome do projeto")
    version = typer.prompt(
        "Digite a versão inicial do projeto",
        "0.1.0",
    )
    description = typer.prompt("Digite a descrição do projeto", "")
    fullname = typer.prompt("Digite seu nome completo", get_default_fullname())
    email = typer.prompt("Digite seu email", get_default_email())
    pyproject_toml = PyprojectToml(
        project_name,
        version,
        description,
        fullname=fullname,
        email=email,
        _dependencies={
            "fastapi",
            "pydantic[email]",
            "uvicorn",
            "aiohttp",
            "python-dotenv",
            "sqlalchemy",
            "aiomysql",
            "circus",
            "gunicorn",
        },
        _dev_dependencies={
            "pytest",
            "pylint",
            "black",
            "pytest-cov",
            "pytest-asyncio",
            "sqlalchemy2-stubs",
        },
        _optional_dependencies={"httptools", "uvloop"},
    )
    typer.echo(typer.style("Creating project structure", fg=typer.colors.GREEN))
    curdir = get_curdir()
    Structure.create(curdir, project_name, pyproject_toml)

    typer.echo(typer.style("Initializing git", fg=typer.colors.GREEN))
    init_repository(curdir / project_name)
    if code:
        if "win" not in sys.platform.lower():
            subprocess.run(["code", project_name])
        else:
            subprocess.run(["code.cmd", project_name])


@app.command("create:table")
def create_table(table_module: str, table_name: str = ""):
    if not table_name:
        table_name = typer.prompt("Digite o nome da tabela")
    curdir = get_curdir()
    tables_dir = find_tables_directory(curdir)
    if not tables_dir:
        typer.echo("Diretório de tabelas não encontrado")
        raise typer.Exit()
    metadata = find_metadata(curdir)
    if not metadata:
        typer.echo("Arquivo de metadata não encontrado")
        raise typer.Exit()
    typer.echo(typer.style("Criando arquivo da tabela"))
    module_file = ModuleFile(tables_dir, table_module, table_name)
    table_file, dunder_file = module_file.retrieve_or_exit()
    typer.echo(typer.style("Escrevendo arquivo da tabela"))
    write_table_file(table_file, tables_dir.parent.parent, table_name)
    typer.echo(typer.style("Atualizando diretório"))
    update_dunder_file(dunder_file)


@app.command("create:dto")
def create_dto(dto_module: str, dto_name: str = ""):
    if not dto_name:
        dto_name = typer.prompt("Digite o nome do DTO")
    curdir = get_curdir()
    dtos_dir = find_dtos_dir(curdir)
    if not dtos_dir:
        typer.echo("Diretório de DTOs não encontrado")
        raise typer.Exit()
    module_file = ModuleFile(dtos_dir, dto_module, dto_name)
    dto_file, dunder_file = module_file.retrieve_or_exit()
    typer.echo(typer.style("Escrevendo arquivo do DTO"))
    write_dto_file(dto_file, dtos_dir.parent, dto_name)
    typer.echo(typer.style("Atualizando diretório"))
    update_dunder_file(dunder_file, camel_public_name_parser)

@app.command("create:enum")
def create_enum(enum_name: str = "", auto_opts: Optional[list[str]] = None):
    if not enum_name:
        enum_name = typer.prompt("Digite o nome do enum")
    curdir = get_curdir()
    dtos_dir = find_dtos_dir(curdir)
    if not dtos_dir:
        typer.echo("Diretório de Enums não encontrado")
        raise typer.Exit()
    module_file = ModuleFile(dtos_dir, "enums", enum_name)
    enum_file, dunder_file = module_file.retrieve_or_exit()
    typer.echo(typer.style("Escrevendo arquivo do Enum"))
    write_enum_file(enum_file, enum_name, auto_opts)
    typer.echo(typer.style("Atualizando diretório"))
    update_dunder_file(dunder_file, camel_public_name_parser)