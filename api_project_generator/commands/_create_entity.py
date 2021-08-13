import pathlib

import typer
from api_project_generator.helpers import files, functions, module_file, strings
from ._create_dto import write_dto_file
from ._create_table import create_table


def create_entity(module: str, name: str, sync: bool):
    curdir = functions.get_curdir()
    db_dir = functions.find_directory(curdir, "database")
    if not db_dir:
        typer.echo(typer.style("Diretório do projeto não foi encontrado"))
        raise typer.Exit()
    project_folder = db_dir.parent
    try:
        functions.prepare_to_import(project_folder)
        _create_dtos(module, name, project_folder)
        _create_table(module, name)
        _create_repository(module, name, project_folder, sync)
    except ImportError:
        typer.echo(typer.style("You didnt installed the packages yet. Run 'poetry install'.", fg=typer.colors.RED))
        raise typer.Exit(0)
    else:
        _create_routes(module, name, project_folder, sync)
    typer.echo("Entidade criada, execute 'api-project update:imports")

def _create_table(module: str, name: str):
    try:
        create_table(module, name)
    except RuntimeError:
        pass


def _create_dtos(module: str, name: str, project_folder: pathlib.Path):
    dtos_dir = project_folder / "dtos"
    if not dtos_dir:
        typer.echo("Diretório de DTOs não encontrado")
        raise typer.Exit()
    for item in [name, f"{name}-in", f"{name}-edit"]:
        _create_dto(dtos_dir, module, item)
    _create_embed_array(dtos_dir, module, name)
    functions.update_module_dunder_file(
        dtos_dir / module / files.Files.python_file("init", dunder=True),
        project_folder,
        functions.dto_inheritance_finder
    )


def _create_dto(dtos_dir: pathlib.Path, module: str, name: str):
    mod = module_file.ModuleFile(dtos_dir, module, name)
    dto_file, _ = mod.retrieve_or_exit()
    typer.echo(typer.style(f"Escrevendo arquivo do DTO: {name}"))
    write_dto_file(dto_file, dtos_dir.parent, name)


def _create_embed_array(dtos_dir: pathlib.Path, module: str, name: str):
    mod = module_file.ModuleFile(dtos_dir, module, f"{name}-embed-array")
    dto_file, _ = mod.retrieve_or_exit()
    entity_snake_case = functions.to_snake(functions.clean_name(name))
    typer.echo(
        typer.style(
            f"Escrevendo arquivo do DTO para listagem de {functions.to_camel(entity_snake_case)}"
        )
    )
    with dto_file.open("w") as stream:
        stream.write(
            strings.BASE_EMBED_ARRAY_BOILERPLATE.format(
                project_folder=dtos_dir.parent.name,
                entity_lower=entity_snake_case,
                entity_name=functions.to_camel(entity_snake_case),
            )
        )


def repository_name_parser(string: str):
    return f"{functions.camel_public_name_parser(string)}Repository"


def _create_repository(
    module: str, name: str, project_folder: pathlib.Path, sync: bool
):
    repository_boilerplate = (
        strings.SYNC_REPOSITORY_BOILERPLATE
        if sync
        else strings.ASYNC_REPOSITORY_BOILERPLATE
    )
    database_dir = project_folder / "database"
    mod = module_file.ModuleFile(database_dir, "repositories", name)
    try:
        repository_file, dunder_file = mod.retrieve_or_exit()
    except RuntimeError:
        return
    else:
        typer.echo(typer.style("Escrevendo arquivo do Repositório"))
        with repository_file.open("w") as stream:
            entity_snake_case = functions.to_snake(functions.clean_name(name))
            stream.write(
                repository_boilerplate.format(
                    project_folder=project_folder.name,
                    module_name=module,
                    table_name=entity_snake_case,
                    entity_name=functions.to_camel(entity_snake_case),
                )
            )
        functions.update_module_dunder_file(dunder_file, project_folder, functions.repo_inheritance_finder)


def routes_name_parser(string: str):
    return f"{functions.to_snake(functions.clean_name(string.removeprefix('_').removesuffix('.py')))}_router"


def _create_routes(module: str, name: str, project_folder: pathlib.Path, sync: bool):
    routes_boilerplate = (
        strings.SYNC_ROUTE_BOILERPLATE if sync else strings.ASYNC_ROUTE_BOILERPLATE
    )
    routes_dir = project_folder / "routes"
    mod = module_file.ModuleFile(routes_dir, module, name)
    try:
        routes_file, dunder_file = mod.retrieve_or_exit()
    except RuntimeError:
        return
    else:
        typer.echo(typer.style("Escrevendo arquivo das Rotas"))
        with routes_file.open("w") as stream:
            entity_snake_case = functions.to_snake(functions.clean_name(name))
            stream.write(
                routes_boilerplate.format(
                    project_folder=project_folder.name,
                    module_name=module,
                    entity_lower=entity_snake_case,
                    entity_name=functions.to_camel(entity_snake_case),
                )
            )
