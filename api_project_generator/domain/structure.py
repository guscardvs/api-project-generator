import re
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unicodedata import normalize

from api_project_generator.domain.models.pyproject_toml import PyprojectToml
from api_project_generator.files import Files
from api_project_generator.functions import get_dependency_string
from api_project_generator.services import strings


class Structure:
    def __init__(
        self, base_dir: Path, project_name: str, pyproject_toml: PyprojectToml
    ) -> None:
        self.files = Files(base_dir / project_name)
        self.project_name = project_name
        self.pyproject_toml = pyproject_toml

    @contextmanager
    def _get_file_stream(self, path: Path, mode: str = "w"):
        with path.open(mode, encoding="utf8") as stream:
            yield stream

    def create_pyproject_toml(self):
        file = self.files.create_file("pyproject.toml")
        with self._get_file_stream(file, "w") as stream:
            stream.write(
                strings.PYPROJECT_TOML.format(
                    **asdict(self.pyproject_toml),
                    project_folder=self._parsed_project_name(),
                    dependencies=self.pyproject_toml.get_dependencies(
                        dev=False, parser=get_dependency_string
                    )
                    + self.pyproject_toml.get_optional_dependencies(
                        parser=lambda lib: get_dependency_string(lib, True)
                    ),
                    dev_dependencies=self.pyproject_toml.get_dependencies(
                        dev=True, parser=get_dependency_string
                    ),
                )
            )

    def _clean_project_name(self):
        return normalize("NFC", self.project_name.strip().replace("-", "_").lower())

    def to_snake(self, name: str):
        return re.sub(
            "([a-z])([A-Z])", lambda match: f"{match[1]}_{match[2]}".lower(), name
        )

    def _parsed_project_name(self):

        return self.to_snake(self._clean_project_name())

    @property
    def project_folder(self):
        return self._parsed_project_name()

    @property
    def dunder_init(self):
        return Files.python_file("__init__")

    @property
    def test_folder(self):
        return "tests"

    @property
    def base_test(self):
        return Files.python_file(f"test_{self.project_folder}")

    @property
    def providers_folder(self):
        return "providers"

    @property
    def core_folder(self):
        return "core"

    @property
    def utils_folder(self):
        return "utils"

    @property
    def main_file(self):
        return Files.python_file("main")

    @property
    def routes_folder(self):
        return "routes"

    @property
    def main_router_file(self):
        return Files.python_file("route", private=True)

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
            Files.python_file(f"test_{self.utils_folder}"), self.test_folder
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
            Files.python_file("http", private=True),
            self.project_folder,
            self.providers_folder,
        )
        database = self.files.create_file(
            Files.python_file("database", private=True),
            self.project_folder,
            self.providers_folder,
        )
        self._populate_providers(dunder, http, database)

    def _populate_providers(self, dunder: Path, http: Path, database: Path):
        with self._get_file_stream(dunder) as stream:
            stream.write(strings.DUNDER_PROVIDER)
        with self._get_file_stream(http) as stream:
            stream.write(
                strings.HTTP_PROVIDER.format(project_folder=self.project_folder)
            )
        with self._get_file_stream(database) as stream:
            stream.write(
                strings.DATABASE_PROVIDER.format(project_folder=self.project_folder)
            )

    def create_core_folder(self):
        self.files.create_dir(self.core_folder, self.project_folder)

    def create_core_files(self):
        self.files.create_file(self.dunder_init, self.project_folder, self.core_folder)
        settings = self.files.create_file(
            Files.python_file("settings"), self.project_folder, self.core_folder
        )
        log = self.files.create_file(
            Files.python_file("log"), self.project_folder, self.core_folder
        )
        self._populate_core_files(settings, log)

    def _populate_core_files(self, settings: Path, log: Path):
        with self._get_file_stream(settings) as stream:
            stream.write(
                strings.SETTINGS_FILE.format(
                    project_folder=self.project_folder, utils_folder=self.utils_folder
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
            Files.python_file("environment", private=True),
            self.project_folder,
            self.utils_folder,
        )
        self._populate_utils_files(dunder, env)

    def _populate_utils_files(self, dunder: Path, env: Path):
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

    def _populate_routes_files(self, dunder: Path, route: Path):
        with self._get_file_stream(dunder) as stream:
            stream.write(
                strings.DUNDER_ROUTES.format(
                    main_router_file=self.main_router_file.removesuffix(".py")
                )
            )
        with self._get_file_stream(route) as stream:
            stream.write(strings.MAIN_ROUTER_FILE)

    def create_dependencies_folder(self):
        self.files.create_dir(
            self.dependencies_folder, self.project_folder, self.routes_folder
        )

    def create_dependencies_files(self):
        path = self.project_folder, self.routes_folder, self.dependencies_folder
        dunder = self.files.create_file(self.dunder_init, *path)
        http = self.files.create_file(Files.python_file("http", private=True), *path)
        database = self.files.create_file(
            Files.python_file("database", private=True), *path
        )
        self._populate_dependencies_files(dunder, http, database)

    def _populate_dependencies_files(self, dunder: Path, http: Path, database: Path):
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
            Files.python_file("base"), self.project_folder, self.dtos_folder
        )
        self._populate_dtos_files(base)

    def _populate_dtos_files(self, base: Path):
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
            Files.python_file("exception_handlers", private=True),
            self.project_folder,
            self.exceptions_folder,
        )
        exceptions = self.files.create_file(
            Files.python_file("exceptions", private=True),
            self.project_folder,
            self.exceptions_folder,
        )
        self._populate_exceptions_files(dunder, handlers, exceptions)

    def _populate_exceptions_files(
        self, dunder: Path, handlers: Path, exceptions: Path
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
            Files.python_file("metadata"), self.project_folder, self.database_folder
        )
        model_finder = self.files.create_file(
            Files.python_file("model_finder", private=True),
            self.project_folder,
            self.database_folder,
        )
        database_main_file = self.files.create_file(
            Files.python_file("main"),
            self.project_folder,
            self.database_folder,
        )
        self.files.create_dir("tables", self.project_folder, self.database_folder)
        self.files.create_file(
            self.dunder_init, self.project_folder, self.database_folder, "tables"
        )
        self._populate_database_files(model_finder, metadata, database_main_file)

    def _populate_database_files(
        self, model_finder: Path, metadata: Path, database_main_file: Path
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

    def create_alembic_folder(self):
        self.files.create_dir(self.alembic_folder)

    def create_alembic_files(self):
        alembic_ini = self.files.create_file("alembic.ini")
        alembic_env = self.files.create_file(
            Files.python_file("env"), self.alembic_folder
        )
        self.files.create_dir("versions", self.alembic_folder)
        alembic_mako = self.files.create_file("script.py.mako", self.alembic_folder)
        alembic_readme = self.files.create_file("README", self.alembic_folder)
        self._populate_alembic_files(
            alembic_ini, alembic_env, alembic_mako, alembic_readme
        )

    def _populate_alembic_files(
        self,
        alembic_ini: Path,
        alembic_env: Path,
        alembic_mako: Path,
        alembic_readme: Path,
    ):
        with self._get_file_stream(alembic_ini) as stream:
            stream.write(strings.ALEMBIC_INI.format(alembic_folder=self.alembic_folder))
        with self._get_file_stream(alembic_env) as stream:
            stream.write(
                strings.ALEMBIC_ENV.format(
                    project_folder=self.project_folder,
                    providers_folder=self.providers_folder,
                    database_folder=self.database_folder,
                )
            )
        with self._get_file_stream(alembic_mako) as stream:
            stream.write(strings.SCRIPT_PY_MAKO)
        with self._get_file_stream(alembic_readme) as stream:
            stream.write(strings.ALEMBIC_README)

    @classmethod
    def create(cls, base_dir: Path, project_name: str, pyproject_toml: PyprojectToml):
        structure = cls(base_dir, project_name, pyproject_toml)

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

        # circus.ini
        structure.create_circus_ini()

        # Database
        structure.create_database_folder()
        structure.create_database_files()

        # Alembic
        structure.create_alembic_folder()
        structure.create_alembic_files()

        return structure
