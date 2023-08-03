import pathlib

import tomlkit
from gyver.attrs import define
from gyver.database import Driver
from gyver.filetree import FileTree
from gyver.utils import lazyfield, strings

from api_project_generator import models
from api_project_generator.commands.create_api import templates
from api_project_generator.core.cache import Cache
from api_project_generator.core.external import get_python_ignore
from api_project_generator.core.local import find_docker_executable, make_local_db
from api_project_generator.core.manifest import append_manifest
from api_project_generator.core.project import project_folders
from api_project_generator.helpers.utils import clean_name, kebab_case


@define
class ApiGeneratorDefaults:
    base_dir: pathlib.Path
    files: FileTree
    pyproject_toml: models.PyprojectToml

    @lazyfield
    def cache(self):
        return Cache(self.project_info.config.default_cache_dir)

    @property
    def project_info(self):
        return self.pyproject_toml.project_info

    @property
    def project_name(self):
        return self.project_info.name

    @property
    def dialect(self):
        return self.project_info.dialect

    @lazyfield
    def project_folder(self):
        with self.files.virtual_context(
            strings.to_snake(clean_name(self.project_name))
        ) as virtual_tree:
            return virtual_tree

    @lazyfield
    def local_dbconfig(self):
        if not self.project_info.driver:
            raise NotImplementedError
        return make_local_db(
            self.project_info.driver,
            self.base_dir / self.project_name,
            kebab_case(self.project_name),
        )

    @lazyfield
    def pyproject_table(self):
        return self.pyproject_toml.make_table(self.project_folder.name)

    def create_pyproject_toml(self):
        file = self.files.create_text_file("pyproject.toml")
        append_manifest(self.pyproject_table, self.project_info)
        contents = tomlkit.dumps(self.pyproject_table)
        contents = "\n".join(contents.split("\n")[1:])
        file.write(contents)

    def setup_project_folder(self):
        self.project_folder.dunder_init().write(
            f'__version__ = "{self.project_info.version}"'
        )

    def create_test_folder(self):
        with self.files.virtual_context(project_folders.tests_folder) as tests_folder:
            tests_folder.dunder_init()
            tests_folder.create_py_file(f"test_{self.project_folder.name}").write(
                templates.BASE_TEST_FILE.render(
                    project_folder=self.project_folder.name,
                    version=self.project_info.version,
                )
            )

    def create_core_folder(self):
        with self.project_folder.virtual_context(
            project_folders.core_folder
        ) as core_folder:
            core_folder.dunder_init()
            core_folder.create_py_file("settings").write(
                templates.SETTINGS_FILE.render(
                    project_folder=self.project_folder.name,
                    db=self.project_info.driver is not None,
                    driver=self.project_info.driver,
                )
            )
            core_folder.create_py_file("log").write(templates.LOG_FILE)

    def create_exceptions_folder(self):
        with self.project_folder.virtual_context(
            project_folders.exceptions_folder
        ) as exceptions_folder:
            exceptions_folder.dunder_init().write(templates.DUNDER_EXC)
            exceptions_folder.create_py_file("handlers").write(
                templates.EXCEPTION_HANDLERS_FILE
            )
            exceptions_folder.create_py_file("exceptions").write(
                templates.EXCEPTIONS_FILE
            )

    def create_api_folder(self):
        with self.project_folder.virtual_context(
            project_folders.api_folder
        ) as api_folder:
            api_folder.dunder_init()
            if self.project_info.driver is None:
                return
            api_folder.create_py_file("database").write(templates.DATABASE_API_FILE)

    def create_main_file(self):
        self.project_folder.create_py_file(project_folders.main_file).write(
            templates.MAIN_FILE.render(
                project_folder=self.project_folder.name,
                project_as_title=self.pyproject_toml.get_project_title(),
                core_folder=project_folders.core_folder,
                exceptions_folder=project_folders.exceptions_folder,
                db=self.project_info.driver is not None,
            )
        )

    def create_ignores(self):
        python_ignore = get_python_ignore(self.cache)
        self.files.create_text_file(".gitignore").write(python_ignore)
        self.files.create_text_file(".dockerignore").write(python_ignore)

    def create_dockerfile(self):
        self.files.create_text_file("Dockerfile").write(
            templates.DOCKERFILE.render(
                pyver=self.project_info.effective_pyver,
                project_folder=self.project_folder.name,
                main_api_file=project_folders.main_file,
            )
        )

    def create_rcs(self):
        with open(pathlib.Path(__file__).parent / "pylintrc.txt") as pylint_file:
            self.files.create_text_file(".pylintrc").write(pylint_file.read())
        self.files.create_text_file(".coveragerc").write(
            templates.COVERAGE_RC.render(project_folder=self.project_folder.name)
        )

    def create_alembic_folder(self):
        if self.project_info.driver is None:
            return
        with self.files.virtual_context(
            project_folders.alembic_folder
        ) as alembic_folder:
            alembic_folder.create_text_file("alembic.ini").write(
                templates.ALEMBIC_INI.render(
                    alembic_folder=project_folders.alembic_folder
                )
            )
            alembic_folder.create_py_file("env").write(
                templates.ALEMBIC_ENV.render(
                    project_folder=self.project_folder.name,
                    core_folder=project_folders.core_folder,
                )
            )
            alembic_folder.create_dir("versions")
            alembic_folder.create_text_file("script.py.mako").write(
                templates.SCRIPT_PY_MAKO
            )
            alembic_folder.create_text_file("README").write(templates.ALEMBIC_README)

    def create_dotenvs(self):
        if not self.project_info.driver:
            return
        local_config = self.local_dbconfig
        self.files.create_text_file(".env-local").write(
            templates.DOTENV_TEMPLATE.render({"db": local_config})
        )
        driver = self.project_info.driver
        dbenvfile = ".env-localdb"
        if driver is Driver.SQLITE:
            return
        elif driver is Driver.POSTGRES:
            self.files.create_text_file(dbenvfile).write(
                templates.POSTGRES_DOTENV.render(db=local_config)
            )
        else:
            self.files.create_text_file(dbenvfile).write(
                templates.MYSQL_COMPAT_DOTENV.render(
                    db_varname=local_config.dialect.dialect_name.upper(),
                    db=local_config,
                )
            )

    def create_makefile(self):
        local_dbconfig = (
            self.local_dbconfig if self.project_info.driver is not None else None
        )
        is_sqlite = self.project_info.driver is Driver.SQLITE
        docker_executable = None if is_sqlite else find_docker_executable()
        self.files.create_text_file("Makefile").write(
            templates.MAKEFILE_TEMPLATE.render(
                project_folder=self.project_name,
                main_file=project_folders.main_file,
                db=local_dbconfig,
                docker_exec=docker_executable,
                not_sqlite=not is_sqlite,
                dialect_name="postgres"
                if self.project_info.driver is Driver.POSTGRES or not local_dbconfig
                else local_dbconfig.dialect.dialect_name,
            )
        )

    def create_defaults(self):
        self.create_pyproject_toml()
        self.setup_project_folder()
        self.create_test_folder()
        self.create_core_folder()
        self.create_exceptions_folder()
        self.create_api_folder()
        self.create_main_file()
        self.create_ignores()
        self.create_dockerfile()
        self.create_rcs()
        self.create_dotenvs()
        self.create_makefile()
        self.create_alembic_folder()
