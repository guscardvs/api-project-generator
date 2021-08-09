import pathlib
from typing import Optional

import typer

from api_project_generator.helpers import functions, module_file, strings


def create_enum(enum_name: str, auto_opts: Optional[list[str]]):
    curdir = functions.get_curdir()
    dtos_dir = find_dtos_dir(curdir)
    if not dtos_dir:
        typer.echo("Diretório de Enums não encontrado")
        raise typer.Exit()
    mod = module_file.ModuleFile(dtos_dir, "enums", enum_name)
    enum_file, dunder_file = mod.retrieve_or_exit()
    typer.echo(typer.style("Escrevendo arquivo do Enum"))
    write_enum_file(enum_file, enum_name, auto_opts)
    typer.echo(typer.style("Atualizando diretório"))
    functions.update_dunder_file(dunder_file, functions.camel_public_name_parser)


def find_dtos_dir(curdir: pathlib.Path):
    return functions.find_directory(curdir, "dtos")


def write_enum_file(
    enum_file: pathlib.Path, enum_name: str, auto_opts: Optional[list[str]]
):
    with enum_file.open("w") as stream:
        stream.write(
            strings.ENUM_TEMPLATE.format(
                enum_name=functions.to_camel(
                    functions.to_snake(functions.clean_name(enum_name))
                ),
                auto_opts="\n    ".join(
                    strings.ENUM_AUTO_OPTS_TEMPLATE.format(
                        opt=opt.upper(), idx=f'"{opt.lower()}"'
                    )
                    for opt in (auto_opts or [])
                ),
            )
        )
