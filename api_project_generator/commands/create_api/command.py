from typing import Optional

import typer
from gyver.filetree import FileTree

from api_project_generator import models
from api_project_generator.commands.create_api.modular import ModularApiGenerator
from api_project_generator.commands.create_api.structure import StructureApiGenerator
from api_project_generator.core import dependencies, dirs, ide
from api_project_generator.models.project_organization import ProjectOrganization


def create_api(open_ide: Optional[str], info: models.ProjectInfo):
    pyproject = models.PyprojectToml(
        info,
        dependencies.DEFAULT_API_DEPENDENCIES,
        dependencies.DEFAULT_DEV_DEPENDENCIES,
        dependencies.DEFAULT_DEPLOY_DEPENDENCIES,
    )
    typer.echo(typer.style("Creating project structure", fg=typer.colors.GREEN))
    curdir = dirs.get_curdir()
    folder = curdir / info.name

    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        typer.echo(
            typer.style(
                "{folder} already exists".format(folder=info.name),
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)
    filetree = FileTree(folder)
    ApiGenerator = (
        StructureApiGenerator
        if info.organization is ProjectOrganization.STRUCTURAL
        else ModularApiGenerator
    )
    with filetree.context():
        ApiGenerator(folder, filetree, pyproject).create()
    if open_ide:
        ide.open_ide(open_ide, folder)
