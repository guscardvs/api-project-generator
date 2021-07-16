import subprocess
import sys

import typer

from api_project_generator.domain.git_repo import init_repository
from api_project_generator.domain.models.pyproject_toml import PyprojectToml
from api_project_generator.domain.structure import Structure
from api_project_generator.domain.tables import (
    create_table_file,
    find_metadata,
    find_tables_directory,
    update_dunder_file,
    write_table_file,
)
from api_project_generator.functions import (
    get_curdir,
    get_default_email,
    get_default_fullname,
)

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


@app.command("create-table")
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
    typer.echo(typer.style("Creating table file"))
    response = create_table_file(tables_dir, table_module, table_name)
    if response is None:
        typer.echo("Módulo é um arquivo e não um diretório ou Arquivo já existe")
        raise typer.Exit()
    table_file, dunder_file = response
    typer.echo(typer.style("Writing table file"))
    write_table_file(table_file, tables_dir.parent.parent, table_name)
    typer.echo(typer.style("Creating table file and/or dir"))
    update_dunder_file(dunder_file)
