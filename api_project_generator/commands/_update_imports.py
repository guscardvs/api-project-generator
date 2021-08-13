import os
from pathlib import Path
from api_project_generator.helpers import files, functions
import typer


def update_imports():
    curdir = functions.get_curdir()
    db_dir = functions.find_directory(curdir, "database")
    if not db_dir:
        typer.echo(typer.style("Diretório do projeto não foi encontrado"))
        raise typer.Exit()
    project_folder = db_dir.parent
    functions.prepare_to_import(project_folder)
    update_dtos(project_folder)
    update_tables(project_folder)
    update_repositories(project_folder)
    update_routes(project_folder)


def ignore_when_running(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except:
        pass


def update_dtos(project_folder: Path):
    for item in (project_folder / "dtos").iterdir():
        if item.is_dir() and "pycache" not in item.name:
            functions.update_module_dunder_file(
                item / files.Files.python_file("init", dunder=True),
                project_folder,
                inheritance_finder=functions.dto_inheritance_finder,
            )


def update_repositories(project_folder: Path):
    functions.update_module_dunder_file(
        project_folder
        / "database"
        / "repositories"
        / files.Files.python_file("init", dunder=True),
        project_folder,
        inheritance_finder=functions.repo_inheritance_finder,
    )


def update_routes(project_folder: Path):
    for item in (project_folder / "routes").iterdir():
        if item.is_dir() and "pycache" not in item.name and item.name != "dependencies":
            functions.update_module_dunder_file(
                item / files.Files.python_file("init", dunder=True),
                project_folder,
                inheritance_finder=functions.routes_inheritance_finder,
            )


def update_tables(project_folder: Path):
    for item in (project_folder / "database" / "tables").iterdir():
        if item.is_dir() and "pycache" not in item.name:
            functions.update_module_dunder_file(
                item / files.Files.python_file("init", dunder=True),
                project_folder,
                inheritance_finder=functions.table_inheritance_finder,
            )
