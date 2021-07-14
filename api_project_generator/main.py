from dataclasses import asdict

import typer

from api_project_generator.domain.models.pyproject_toml import PyprojectToml
from api_project_generator.domain.structure import Structure
from api_project_generator.functions import (
    get_curdir,
    get_default_email,
    get_default_fullname,
)

from .application import get_application

app = get_application()


@app.command()
def create():
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
    Structure.create(get_curdir(), project_name, pyproject_toml)
