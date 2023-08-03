import pathlib

from gyver.attrs import define
from gyver.filetree import FileTree
from gyver.utils import lazyfield

from api_project_generator import models
from api_project_generator.commands.create_api.defaults import ApiGeneratorDefaults
from api_project_generator.core.project import project_folders

from . import templates


@define
class StructureApiGenerator:
    base_dir: pathlib.Path
    files: FileTree
    pyproject_toml: models.PyprojectToml

    @lazyfield
    def defaults(self):
        return ApiGeneratorDefaults(self.base_dir, self.files, self.pyproject_toml)

    @property
    def project_name(self):
        return self.project_info.name

    @property
    def dialect(self):
        return self.defaults.dialect

    @property
    def project_info(self):
        return self.pyproject_toml.project_info

    @property
    def project_folder(self):
        return self.defaults.project_folder

    @property
    def local_dbconfig(self):
        return self.defaults.local_dbconfig

    def create_routes_folder(self):
        with self.project_folder.virtual_context(
            project_folders.routes_name
        ) as routes_folder:
            routes_folder.dunder_init().write(
                templates.DUNDER_ROUTES.render(
                    main_router_file=project_folders.main_router_file
                )
            )
            routes_folder.create_py_file(project_folders.main_router_file).write(
                templates.MAIN_ROUTER_FILE
            )

    def create_schemas_folder(self):
        with self.project_folder.virtual_context(
            project_folders.schemas_name
        ) as schemas_folder:
            schemas_folder.dunder_init()
            schemas_folder.create_py_file(project_folders.commons).write(
                templates.BASE_SCHEMA_FILE
            )

    def create(self):
        self.defaults.create_defaults()
        self.create_routes_folder()
        self.create_schemas_folder()
