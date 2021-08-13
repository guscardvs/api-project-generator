from typing import Optional

import typer

from api_project_generator import commands
from api_project_generator.models import project_info

from .application import get_application
from .helpers import functions

app = get_application()


@app.command("create:api")
def create(
    db_type: project_info.DbType = typer.Option(project_info.DbType.MYSQL),
    code: bool = typer.Option(False),
):
    project_name = typer.prompt("Digite o nome do projeto")
    version = typer.prompt(
        "Digite a versão inicial do projeto",
        "0.1.0",
    )
    description = typer.prompt("Digite a descrição do projeto", "")
    fullname = typer.prompt(
        "Digite seu nome completo", functions.get_default_fullname()
    )
    email = typer.prompt("Digite seu email", functions.get_default_email())
    typer
    return commands.create_api(
        code,
        project_info.ProjectInfo(
            project_name, version, description, fullname, email, db_type
        ),
    )


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
def create_entity(module: str, name: str = typer.Argument(""), sync: bool = typer.Option(False)):
    if not name:
        name = typer.prompt("Digite o nome da entidade")
    return commands.create_entity(module, name, sync)

@app.command("update:imports")
def update_imports():
    return commands.update_imports()