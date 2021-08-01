import pathlib
from api_project_generator.helpers import functions, module_file, strings
import typer


def create_dto(dto_module: str, dto_name: str):
    curdir = functions.get_curdir()
    dtos_dir = find_dtos_dir(curdir)
    if not dtos_dir:
        typer.echo("Diretório de DTOs não encontrado")
        raise typer.Exit()
    mod = module_file.ModuleFile(dtos_dir, dto_module, dto_name)
    dto_file, dunder_file = mod.retrieve_or_exit()
    typer.echo(typer.style("Escrevendo arquivo do DTO"))
    write_dto_file(dto_file, dtos_dir.parent, dto_name)
    typer.echo(typer.style("Atualizando diretório"))
    functions.update_dunder_file(dunder_file, functions.camel_public_name_parser)


def find_dtos_dir(path: pathlib.Path):
    return functions.find_directory(path, "dtos")


def write_dto_file(dto_file: pathlib.Path, project_folder: pathlib.Path, dto_name: str):
    with dto_file.open("w") as stream:
        stream.write(
            strings.DTO_TEMPLATE.format(
                project_folder=project_folder.name,
                dto_name=functions.to_camel(
                    functions.to_snake(functions.clean_name(dto_name))
                ),
            )
        )
