import contextlib
import dataclasses
import pathlib

import typer

from api_project_generator.helpers import (
    dependencies,
    files,
    functions,
    git_repo,
    strings,
)
from api_project_generator.models import project_info, pyproject_toml


def create_api(code: bool, info: project_info.ProjectInfo):
    pyproject = pyproject_toml.PyprojectToml(
        info.name,
        info.version,
        info.description,
        db_type=info.db_type,
        fullname=info.fullname,
        email=info.email,
        _dependencies=dependencies.DEFAULT_API_DEPENDENCIES,
        _dev_dependencies=dependencies.DEFAULT_DEV_DEPENDENCIES,
        _optional_dependencies=dependencies.DEFAULT_DEPLOY_DEPENDENCIES,
    )
    typer.echo(typer.style("Creating project structure", fg=typer.colors.GREEN))
    curdir = functions.get_curdir()
    folder = (curdir / info.name)
    while folder.exists():
        if folder.is_dir():
            if not any(folder.iterdir()):
                break
        typer.echo(typer.style("{folder} already exists".format(folder=info.name), fg=typer.colors.RED))
        raise typer.Exit(1)
    ApiStructure.create(curdir, info.name, pyproject, info.db_type)

    typer.echo(typer.style("Initializing git", fg=typer.colors.GREEN))
    git_repo.init_repository(curdir / info.name)
    if code:
        result = functions.open_in_code(info.name)
        if not result:
            typer.echo(typer.style("Could not open code", fg=typer.colors.RED))


class ApiStructure:
    def __init__(
        self,
        base_dir: pathlib.Path,
        project_name: str,
        pyproject_toml: pyproject_toml.PyprojectToml,
        db_type: project_info.DbType,
    ) -> None:
        self.files = files.Files(base_dir / project_name)
        self.project_name = project_name
        self.pyproject_toml = pyproject_toml
        self.db_type = db_type

    @contextlib.contextmanager
    def _get_file_stream(self, path: pathlib.Path, mode: str = "w"):
        with path.open(mode, encoding="utf8") as stream:
            yield stream

    def create_pyproject_toml(self):
        file = self.files.create_file("pyproject.toml")
        with self._get_file_stream(file, "w") as stream:
            stream.write(
                strings.PYPROJECT_TOML.format(
                    **dataclasses.asdict(self.pyproject_toml),
                    project_folder=self._parsed_project_name(),
                    dependencies=self.pyproject_toml.get_dependencies(
                        dev=False,
                        parser=functions.get_dependency_string,
                    )
                    + self.pyproject_toml.get_optional_dependencies(
                        parser=lambda lib: functions.get_dependency_string(lib, True)
                    ),
                    dev_dependencies=self.pyproject_toml.get_dependencies(
                        dev=True, parser=functions.get_dependency_string
                    ),
                    optional_dependencies=", ".join(f'"{item}"' for item in self.pyproject_toml.optional_dependencies)
                )
            )

    def _parsed_project_name(self):
        return functions.to_snake(functions.clean_name(self.project_name))

    @property
    def project_folder(self):
        return self._parsed_project_name()

    @property
    def dunder_init(self):
        return files.Files.python_file("__init__")

    @property
    def test_folder(self):
        return "tests"

    @property
    def base_test(self):
        return files.Files.python_file(f"test_{self.project_folder}")

    @property
    def providers_folder(self):
        return "providers"

    @property
    def core_folder(self):
        return "core"

    @property
    def utils_folder(self):
        return "helpers"

    @property
    def main_file(self):
        return files.Files.python_file("main")

    @property
    def routes_folder(self):
        return "routes"

    @property
    def main_router_file(self):
        return files.Files.python_file("route", private=True)

    @property
    def dependencies_folder(self):
        return "dependencies"

    @property
    def dtos_folder(self):
        return "dtos"

    @property
    def domain_folder(self):
        return "domain"

    @property
    def exceptions_folder(self):
        return "exc"

    @property
    def database_folder(self):
        return "database"

    @property
    def alembic_folder(self):
        return "alembic"

    def create_project_folder(self):
        self.files.create_dir(self.project_folder)
        self.files.create_file(self.dunder_init, self.project_folder)

    def add_version_to_dunder_project(self):
        file = self.files.get_file(self.dunder_init, self.project_folder)
        with self._get_file_stream(file) as stream:
            stream.write(f'__version__ = "{self.pyproject_toml.version}"')

    def create_test_folder(self):
        self.files.create_dir(self.test_folder)
        self.files.create_file(self.dunder_init, self.test_folder)

    def create_base_test_file(self):
        self.files.create_file(
            self.base_test,
            self.test_folder,
        )

    def add_test_to_base_test_file(self):
        file = self.files.get_file(self.base_test, self.test_folder)
        with self._get_file_stream(file) as stream:
            stream.write(
                strings.BASE_TEST_FILE.format(
                    project_folder=self._parsed_project_name(),
                    version=self.pyproject_toml.version,
                )
            )

    def create_utils_test_file(self):
        file = self.files.create_file(
            files.Files.python_file(f"test_{self.utils_folder}"), self.test_folder
        )
        with self._get_file_stream(file) as stream:
            stream.write(
                strings.TEST_UTILS.format(
                    project_folder=self.project_folder,
                    exceptions_folder=self.exceptions_folder,
                    utils_folder=self.utils_folder,
                )
            )

    def create_providers_folder(self):
        self.files.create_dir(self.providers_folder, self.project_folder)

    def create_providers_files(self):
        dunder = self.files.create_file(
            self.dunder_init,
            self.project_folder,
            self.providers_folder,
        )
        http = self.files.create_file(
            files.Files.python_file("http", private=True),
            self.project_folder,
            self.providers_folder,
        )
        database = self.files.create_file(
            files.Files.python_file("database", private=True),
            self.project_folder,
            self.providers_folder,
        )
        self._populate_providers(dunder, http, database)

    def _populate_providers(
        self, dunder: pathlib.Path, http: pathlib.Path, database: pathlib.Path
    ):
        with self._get_file_stream(dunder) as stream:
            stream.write(strings.DUNDER_PROVIDER)
        with self._get_file_stream(http) as stream:
            stream.write(
                strings.HTTP_PROVIDER.format(project_folder=self.project_folder)
            )
        with self._get_file_stream(database) as stream:
            stream.write(
                strings.DATABASE_PROVIDER.format(
                    project_folder=self.project_folder,
                    db_type=self.db_type.name,
                )
            )

    def create_core_folder(self):
        self.files.create_dir(self.core_folder, self.project_folder)

    def create_core_files(self):
        self.files.create_file(self.dunder_init, self.project_folder, self.core_folder)
        settings = self.files.create_file(
            files.Files.python_file("settings"), self.project_folder, self.core_folder
        )
        log = self.files.create_file(
            files.Files.python_file("log"), self.project_folder, self.core_folder
        )
        self._populate_core_files(settings, log)

    def _populate_core_files(self, settings: pathlib.Path, log: pathlib.Path):
        with self._get_file_stream(settings) as stream:
            stream.write(
                strings.SETTINGS_FILE.format(
                    project_folder=self.project_folder,
                    utils_folder=self.utils_folder,
                    db_port=self.db_type.get_db_port(),
                )
            )
        with self._get_file_stream(log) as stream:
            stream.write(
                strings.LOG_FILE.format(
                    project_folder=self.project_folder, utils_folder=self.utils_folder
                )
            )

    def create_utils_folder(self):
        self.files.create_dir(self.utils_folder, self.project_folder)

    def create_utils_files(self):
        dunder = self.files.create_file(
            self.dunder_init, self.project_folder, self.utils_folder
        )
        env = self.files.create_file(
            files.Files.python_file("environment", private=True),
            self.project_folder,
            self.utils_folder,
        )
        self._populate_utils_files(dunder, env)

    def _populate_utils_files(self, dunder: pathlib.Path, env: pathlib.Path):
        with self._get_file_stream(dunder) as stream:
            stream.write(strings.DUNDER_UTILS)
        with self._get_file_stream(env) as stream:
            stream.write(
                strings.ENVIRONMENT_FILE.format(
                    project_folder=self.project_folder,
                    exceptions_folder=self.exceptions_folder,
                )
            )

    def create_routes_folder(self):
        self.files.create_dir(self.routes_folder, self.project_folder)

    def create_routes_files(self):
        dunder = self.files.create_file(
            self.dunder_init, self.project_folder, self.routes_folder
        )
        route = self.files.create_file(
            self.main_router_file, self.project_folder, self.routes_folder
        )
        self._populate_routes_files(dunder, route)

    def _populate_routes_files(self, dunder: pathlib.Path, route: pathlib.Path):
        with self._get_file_stream(dunder) as stream:
            stream.write(
                strings.DUNDER_ROUTES.format(
                    main_router_file=self.main_router_file.removesuffix(".py")
                )
            )
        with self._get_file_stream(route) as stream:
            stream.write(
                strings.MAIN_ROUTER_FILE.format(
                    project_folder=self.project_folder,
                    providers_folder=self.providers_folder,
                )
            )

    def create_dependencies_folder(self):
        self.files.create_dir(
            self.dependencies_folder, self.project_folder, self.routes_folder
        )

    def create_dependencies_files(self):
        path = self.project_folder, self.routes_folder, self.dependencies_folder
        dunder = self.files.create_file(self.dunder_init, *path)
        http = self.files.create_file(
            files.Files.python_file("http", private=True), *path
        )
        database = self.files.create_file(
            files.Files.python_file("database", private=True), *path
        )
        self._populate_dependencies_files(dunder, http, database)

    def _populate_dependencies_files(
        self, dunder: pathlib.Path, http: pathlib.Path, database: pathlib.Path
    ):
        with self._get_file_stream(dunder) as stream:
            stream.write(strings.DUNDER_DEPENDENCIES)
        with self._get_file_stream(http) as stream:
            stream.write(
                strings.HTTP_DEPENDENCY_FILE.format(
                    project_folder=self.project_folder,
                    providers_folder=self.providers_folder,
                )
            )
        with self._get_file_stream(database) as stream:
            stream.write(
                strings.DATABASE_DEPENDENCY_FILE.format(
                    project_folder=self.project_folder,
                    providers_folder=self.providers_folder,
                )
            )

    def create_dtos_folder(self):
        self.files.create_dir(self.dtos_folder, self.project_folder)

    def create_dtos_files(self):
        self.files.create_file(self.dunder_init, self.project_folder, self.dtos_folder)
        base = self.files.create_file(
            files.Files.python_file("base"), self.project_folder, self.dtos_folder
        )
        self.files.create_dir("enums", self.project_folder, self.dtos_folder)
        self.files.create_file(
            self.dunder_init, self.project_folder, self.dtos_folder, "enums"
        )
        self._populate_dtos_files(base)

    def _populate_dtos_files(self, base: pathlib.Path):
        with self._get_file_stream(base) as stream:
            stream.write(strings.BASE_DTO_FILE)

    def create_domain_folder(self):
        self.files.create_dir(self.domain_folder, self.project_folder)

    def create_domain_files(self):
        self.files.create_file(
            self.dunder_init, self.project_folder, self.domain_folder
        )

    def create_exceptions_folder(self):
        self.files.create_dir(self.exceptions_folder, self.project_folder)

    def create_exceptions_files(self):
        dunder = self.files.create_file(
            self.dunder_init, self.project_folder, self.exceptions_folder
        )
        handlers = self.files.create_file(
            files.Files.python_file("exception_handlers", private=True),
            self.project_folder,
            self.exceptions_folder,
        )
        exceptions = self.files.create_file(
            files.Files.python_file("exceptions", private=True),
            self.project_folder,
            self.exceptions_folder,
        )
        self._populate_exceptions_files(dunder, handlers, exceptions)

    def _populate_exceptions_files(
        self, dunder: pathlib.Path, handlers: pathlib.Path, exceptions: pathlib.Path
    ):
        with self._get_file_stream(dunder) as stream:
            stream.write(strings.DUNDER_EXC)
        with self._get_file_stream(handlers) as stream:
            stream.write(strings.EXCEPTION_HANDLERS_FILE)
        with self._get_file_stream(exceptions) as stream:
            stream.write(strings.EXCEPTIONS_FILE)

    def create_main_file(self):
        file = self.files.create_file(self.main_file, self.project_folder)
        with self._get_file_stream(file) as stream:
            stream.write(
                strings.MAIN_FILE.format(
                    project_folder=self.project_folder,
                    providers_folder=self.providers_folder,
                    exceptions_folder=self.exceptions_folder,
                    project_as_title=self.pyproject_toml.get_project_title(),
                )
            )

    def create_ignores(self):
        git = self.files.create_file(".gitignore")
        docker = self.files.create_file(".dockerignore")
        with self._get_file_stream(git) as stream:
            stream.write(strings.GITIGNORE_FILE)
        with self._get_file_stream(docker) as stream:
            stream.write(strings.GITIGNORE_FILE)

    def create_dockerfile(self):
        file = self.files.create_file("Dockerfile")
        with self._get_file_stream(file) as stream:
            stream.write(strings.DOCKERFILE)

    def create_pylintrc(self):
        file = self.files.create_file(".pylintrc")
        with self._get_file_stream(file) as stream:
            stream.write(strings.PYLINTRC)

    def create_circus_ini(self):
        file = self.files.create_file("circus.ini")
        with self._get_file_stream(file) as stream:
            stream.write(
                strings.CIRCUS_INI.format(
                    project_name=self.pyproject_toml.project_name,
                    project_folder=self.project_folder,
                )
            )

    def create_coveragerc(self):
        file = self.files.create_file(".coveragerc")
        with self._get_file_stream(file) as stream:
            stream.write(strings.COVERAGE_RC.format(project_folder=self.project_folder))

    def create_database_folder(self):
        self.files.create_dir(self.database_folder, self.project_folder)

    def create_database_files(self):
        self.files.create_file(
            self.dunder_init, self.project_folder, self.database_folder
        )
        metadata = self.files.create_file(
            files.Files.python_file("metadata"),
            self.project_folder,
            self.database_folder,
        )
        model_finder = self.files.create_file(
            files.Files.python_file("model_finder", private=True),
            self.project_folder,
            self.database_folder,
        )
        database_main_file = self.files.create_file(
            files.Files.python_file("main"),
            self.project_folder,
            self.database_folder,
        )
        database_filters_file = self.files.create_file(
            files.Files.python_file("filters"),
            self.project_folder,
            self.database_folder,
        )
        database_helpers_file = self.files.create_file(
            files.Files.python_file("helpers"),
            self.project_folder,
            self.database_folder,
        )
        self.files.create_dir("tables", self.project_folder, self.database_folder)
        self.files.create_file(
            self.dunder_init, self.project_folder, self.database_folder, "tables"
        )
        self._populate_database_files(
            model_finder,
            metadata,
            database_main_file,
            database_filters_file,
            database_helpers_file,
        )

    def _populate_database_files(
        self,
        model_finder: pathlib.Path,
        metadata: pathlib.Path,
        database_main_file: pathlib.Path,
        database_filters_file: pathlib.Path,
        database_helpers_file: pathlib.Path,
    ):
        with self._get_file_stream(metadata) as stream:
            stream.write(strings.METADATA_FILE)
        with self._get_file_stream(model_finder) as stream:
            stream.write(strings.MODEL_FINDER_FILE)
        with self._get_file_stream(database_main_file) as stream:
            stream.write(
                strings.DATABASE_MAIN_FILE.format(
                    project_folder=self.project_folder, core_folder=self.core_folder
                )
            )
        with self._get_file_stream(database_filters_file) as stream:
            stream.write(strings.DATABASE_FILTERS)
        with self._get_file_stream(database_helpers_file) as stream:
            stream.write(
                strings.DATABASE_HELPERS_FILE.format(project_folder=self.project_folder)
            )

    def create_alembic_folder(self):
        self.files.create_dir(self.alembic_folder)

    def create_alembic_files(self):
        alembic_ini = self.files.create_file("alembic.ini")
        alembic_env = self.files.create_file(
            files.Files.python_file("env"), self.alembic_folder
        )
        self.files.create_dir("versions", self.alembic_folder)
        alembic_mako = self.files.create_file("script.py.mako", self.alembic_folder)
        alembic_readme = self.files.create_file("README", self.alembic_folder)
        self._populate_alembic_files(
            alembic_ini, alembic_env, alembic_mako, alembic_readme
        )

    def _populate_alembic_files(
        self,
        alembic_ini: pathlib.Path,
        alembic_env: pathlib.Path,
        alembic_mako: pathlib.Path,
        alembic_readme: pathlib.Path,
    ):
        with self._get_file_stream(alembic_ini) as stream:
            stream.write(strings.ALEMBIC_INI.format(alembic_folder=self.alembic_folder))
        with self._get_file_stream(alembic_env) as stream:
            stream.write(
                strings.ALEMBIC_ENV.format(
                    project_folder=self.project_folder,
                    providers_folder=self.providers_folder,
                    database_folder=self.database_folder,
                    db_type=self.db_type.name,
                )
            )
        with self._get_file_stream(alembic_mako) as stream:
            stream.write(strings.SCRIPT_PY_MAKO)
        with self._get_file_stream(alembic_readme) as stream:
            stream.write(strings.ALEMBIC_README)

    def create_dotenv(self):
        dotenv = self.files.create_file(".env")
        with self._get_file_stream(dotenv) as stream:
            stream.write(strings.DOTENV)

    @classmethod
    def create(
        cls,
        base_dir: pathlib.Path,
        project_name: str,
        pyproject_toml: pyproject_toml.PyprojectToml,
        db_type: project_info.DbType,
    ):
        structure = cls(base_dir, project_name, pyproject_toml, db_type)

        # Pyproject.toml
        structure.create_pyproject_toml()

        # Base Folder
        structure.create_project_folder()
        structure.add_version_to_dunder_project()

        # Test Folder
        structure.create_test_folder()
        structure.create_base_test_file()
        structure.add_test_to_base_test_file()

        # Providers
        structure.create_providers_folder()
        structure.create_providers_files()

        # Core
        structure.create_core_folder()
        structure.create_core_files()

        # Utils
        structure.create_utils_folder()
        structure.create_utils_files()

        # Routes
        structure.create_routes_folder()
        structure.create_routes_files()

        # Dependencies
        structure.create_dependencies_folder()
        structure.create_dependencies_files()

        # DTOs
        structure.create_dtos_folder()
        structure.create_dtos_files()

        # Domain
        structure.create_domain_folder()
        structure.create_domain_files()

        # Exceptions
        structure.create_exceptions_folder()
        structure.create_exceptions_files()

        # main.py
        structure.create_main_file()

        # .gitignore
        structure.create_ignores()

        # Dockerfile
        structure.create_dockerfile()

        # .coveragerc
        structure.create_coveragerc()

        # .pylintrc
        structure.create_pylintrc()

        # circus.ini
        structure.create_circus_ini()

        # Database
        structure.create_database_folder()
        structure.create_database_files()

        # Alembic
        structure.create_alembic_folder()
        structure.create_alembic_files()

        # .env
        structure.create_dotenv()

        return structure
