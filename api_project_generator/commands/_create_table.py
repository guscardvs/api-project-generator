import pathlib
from typing import Optional

import typer

from api_project_generator.helpers import files, functions, module_file, strings


def create_table(table_module: str, table_name: str):
    curdir = functions.get_curdir()
    tables_dir = find_tables_directory(curdir)
    if not tables_dir:
        typer.echo("Diretório de tabelas não encontrado")
        raise typer.Exit()
    metadata = find_metadata(curdir)
    if not metadata:
        typer.echo("Arquivo de metadata não encontrado")
        raise typer.Exit()
    typer.echo(typer.style("Criando arquivo da tabela"))
    mod = module_file.ModuleFile(tables_dir, table_module, table_name)
    table_file, dunder_file = mod.retrieve_or_exit()
    typer.echo(typer.style("Escrevendo arquivo da tabela"))
    write_table_file(table_file, tables_dir.parent.parent, table_name)
    typer.echo(typer.style("Atualizando diretório"))
    functions.update_dunder_file(dunder_file)


def find_tables_directory(path: pathlib.Path):
    return functions.find_directory(path, "tables")


def find_metadata(curdir: pathlib.Path) -> Optional[pathlib.Path]:
    tables_dir = find_tables_directory(curdir)
    if not tables_dir:
        return None
    metadata = tables_dir.parent / files.Files.python_file("metadata")
    if metadata.exists():
        return metadata
    return None


def write_table_file(file: pathlib.Path, project_folder: pathlib.Path, table_name: str):
    with file.open("w") as stream:
        stream.write(
            strings.TABLE_TEMPLATE.format(
                project_folder=project_folder.name,
                table_normalized_name=functions.to_snake(
                    functions.clean_name(table_name)
                ),
                table_name=table_name,
            )
        )
