PYPROJECT_TOML = """[tool.poetry]
name = "{project_name}"
version = "{version}"
description = "{description}"
authors = ["{fullname} <{email}>"]

[tool.poetry.dependencies]
{dependencies}

[tool.poetry.dev-dependencies]
{dev_dependencies}

[tool.poetry.scripts]
start = "{project_folder}.main:main"

[tool.poetry.extras]
deploy = [{optional_dependencies}]

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

"""

BASE_TEST_FILE = """from {project_folder} import __version__

def test_{project_folder}():
    assert __version__ == "{version}"

"""

DUNDER_PROVIDER = """from ._http import HttpProvider
from ._database import DatabaseProvider, DriverTypes

__all__ = ["HttpProvider", "DatabaseProvider", "DriverTypes"]

"""

HTTP_PROVIDER = """import asyncio
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Callable, Optional, TypeVar
from urllib.parse import urlparse

from {project_folder}.core.settings import logger
from aiohttp import ClientSession, ContentTypeError
from typing_extensions import Concatenate, ParamSpec

_Params = ParamSpec("_Params")
_Return = TypeVar("_Return")


def loaded_wrapper(
    func: Callable[Concatenate["HttpProvider", _Params], _Return]
) -> Callable[Concatenate["HttpProvider", _Params], _Return]:
    @wraps(func)
    def inner(self: "HttpProvider", *args: _Params.args, **kwargs: _Params.kwargs):
        if not self.loaded:
            logger.warning(
                "Executing Session manager without loading it, starting it now."
            )
            self.init()
        return func(self, *args, **kwargs)

    return inner


class HttpProvider:
    def __init__(self):
        self.loaded = False
        self.init()

    def init(self):
        if self.loaded:
            return
        logger.info("Starting HTTP Session Manager")
        self.clients: dict[str, ClientSession] = {{}}
        self._get_client("http://default")
        self.loaded = True

    @loaded_wrapper
    async def finish(self):
        logger.info("Stopping HTTP Session Manager")
        await asyncio.gather(*[value.close() for value in self.clients.values()])
        self.loaded = False

    def _get_client(self, url: str):
        name = urlparse(url).netloc
        if client := self.clients.get(name):
            return client
        self.clients[name] = ClientSession()
        return self.clients[name]

    @loaded_wrapper
    def get_client(self, url: str):
        return self._get_client(url)

    @asynccontextmanager
    async def request(
        self, method: str, url: str, **kwargs
    ) -> AsyncGenerator[tuple[dict[str, Any], int], None]:
        async with self.get_client(url).request(method, url, **kwargs) as response:
            try:
                yield (await response.json(encoding="utf8"), response.status)
            except ContentTypeError:
                pass

    def get(self, url: str, *, params: dict[str, Any] = None, **kwargs):
        return self.request("GET", url, params=params or {{}}, **kwargs)

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] = None,
        data: dict[str, Any] = None,
        **kwargs,
    ):
        if json:
            return self.request("POST", url, json=json or {{}}, **kwargs)
        return self.request("POST", url, data=data or {{}}, **kwargs)

"""

DATABASE_PROVIDER = """from contextlib import asynccontextmanager, contextmanager
import enum
from typing import Optional

from {project_folder}.core import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine, text

class DriverTypes(enum.Enum):
    POSTGRES = ("postgresql", "asyncpg", "psycopg2")
    MYSQL = ("mysql", "aiomysql", "pymysql")

    def get_driver_string(self, is_async: bool):
        name, aio, sync = self.value
        return "{{name}}+{{driver}}".format(name=name, driver=aio if is_async else sync)


class DatabaseProvider:
    def __init__(self, conn_uri: Optional[str] = None) -> None:
        self.engine, self.sync_engine = self._create_engine(conn_uri)

    @staticmethod
    def get_connection_uri(driver: str):
        return "{{driver}}://{{user}}:{{passwd}}@{{host}}:{{port}}/{{name}}".format(
            driver=driver,
            user=settings.DB_USER,
            passwd=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            name=settings.DB_NAME,
            port=settings.DB_PORT,
        )

    @classmethod
    def get_driver_conn_uri(cls, driver: DriverTypes, is_async: bool):
        return cls.get_connection_uri(driver.get_driver_string(is_async))

    def _create_engine(self, conn_uri: Optional[str]):
        if conn_uri:
            return create_async_engine(conn_uri), create_engine(conn_uri)
        return create_async_engine(
            self.get_driver_conn_uri(DriverTypes.{db_type}, is_async=True), pool_size=20, max_overflow=0
        ), create_engine(self.get_driver_conn_uri(DriverTypes.{db_type}, is_async=False), pool_size=20, max_overflow=0)

    @asynccontextmanager
    async def begin(self):
        async with self.engine.begin() as conn:
            yield conn
    
    @contextmanager
    def sync(self):
        with self.sync_engine.begin() as conn:
            yield conn

    async def healthcheck(self):
        try:
            async with self.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except:
            settings.logger.exception()
            return False
        
    def sync_healthcheck(self):
        try:
            with self.sync() as conn:
                conn.execute(text("SELECT 1"))
            return False
        except:
            settings.logger.exception()
            return False


"""

SETTINGS_FILE = """
from pathlib import Path

from dotenv import load_dotenv

from {project_folder}.core.log import set_logger
from {project_folder}.{utils_folder} import Env, Environment

BASE_DIR = Path(__file__).resolve().parent.parent
if (env_file:=(BASE_DIR.parent / ".env")).exists():
    load_dotenv(env_file)

environment = Environment()
ENV = environment.get("ENV", dev="dev", parser=Env)
required_env = environment.required_if(ENV == Env.PROD)
logger = set_logger(ENV)
environment.set_logger(logger)

DB_NAME = environment.get("DB_NAME", dev="db-name")
DB_USER = required_env("DB_USER", dev="db-user")
DB_PASSWORD = required_env("DB_PASSWORD", dev="db-pass")
DB_HOST = required_env("DB_HOST", dev="localhost")
DB_PORT = environment.get("DB_PORT", dev="{db_port}", parser=int)

"""

LOG_FILE = """import logging

from {project_folder}.{utils_folder} import Env


def set_logger(env: Env):
    logger = logging.getLogger("uvicorn.error" if env != Env.PROD else "gunicorn.error")
    logger.setLevel(logging.INFO)
    return logger

"""

DUNDER_UTILS = """from ._environment import Env, Environment
__all__ = ["Env", "Environment"]

"""

ENVIRONMENT_FILE = """from enum import Enum
from logging import Logger
from os import getenv
from typing import Callable, Optional, TypeVar

from {project_folder}.{exceptions_folder} import EnvironmentNotSet


class Env(str, Enum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


T = TypeVar("T")


class Environment:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.__logger = logger

    @property
    def logger(self):
        return self.__logger

    def set_logger(self, logger: Logger):
        self.__logger = logger

    @staticmethod
    def default_parser(val: str) -> str:
        return val

    def _get(
        self,
        cond: bool,
        key: str,
        *,
        dev: str,
        parser: Optional[Callable[[str], T]] = None,
        fallback: Callable,
    ) -> T:
        val = getenv(key)
        if not val and cond:
            fallback()
        return (parser or self.default_parser)(val or dev)  # type: ignore

    def required(
        self,
        cond: bool,
        key: str,
        *,
        dev: str,
        parser: Optional[Callable[[str], T]] = None,
    ) -> T:
        def fallback():
            raise EnvironmentNotSet(key)

        return self._get(cond, key, dev=dev, parser=parser, fallback=fallback)

    def get(
        self, key: str, *, dev: str, parser: Optional[Callable[[str], T]] = None
    ) -> T:
        def fallback():
            if self.logger is not None:
                self.logger.warning(f"The key {{key}} is not set.")

        return self._get(
            True,
            key,
            dev=dev,
            parser=parser,
            fallback=fallback,
        )

    def required_if(self, cond: bool):
        def _required(
            key: str,
            *,
            dev: str,
            parser: Optional[Callable[[str], T]] = None,
        ) -> T:
            return self.required(cond, key, dev=dev, parser=parser)

        return _required

"""

DUNDER_ROUTES = """from .{main_router_file} import router


__all__ = ["router"] 
"""

MAIN_ROUTER_FILE = """from fastapi import APIRouter, Depends

from {project_folder}.{providers_folder} import DatabaseProvider
from .dependencies import get_database_provider

router = APIRouter()

@router.get("/health")
async def validate_health(database_provider: DatabaseProvider = Depends(get_database_provider)):
    return {{"status":await database_provider.healthcheck()}}

"""

DUNDER_DEPENDENCIES = """from ._http import get_http_provider
from ._database import get_database_provider

__all__ =["get_http_provider", "get_database_provider"]

"""

HTTP_DEPENDENCY_FILE = """from fastapi import Request
from {project_folder}.{providers_folder} import HttpProvider

def get_http_provider(request: Request) -> HttpProvider:
    return request.app.state.http_provider

"""

DATABASE_DEPENDENCY_FILE = """from fastapi import Request
from {project_folder}.{providers_folder} import DatabaseProvider

def get_database_provider(request: Request) -> DatabaseProvider:
    return request.app.state.database_provider

"""

BASE_DTO_FILE = """import re
from typing import Generic, TypeVar, TYPE_CHECKING

from pydantic import BaseModel, create_model

_to_camel_exp = re.compile("_([a-zA-Z])")


class DTO(BaseModel):
    class Config:
        allow_population_by_field_name = True
        allow_mutation = False
        use_enum_values = True

        @classmethod
        def alias_generator(cls, string):
            return re.sub(_to_camel_exp, lambda match: match[1].upper(), string)

if TYPE_CHECKING:
    DTO_T = TypeVar("DTO_T", bound=DTO)


    class _EmbedArray(Generic[DTO_T]):
        data: list[DTO_T]


def embed_array(dto: "type[DTO_T]", mod: str) -> "_EmbedArray[DTO_T]":
    return create_model(f"{dto.__qualname__}EmbedArray", __module__=mod, data=(list[dto], ...))  # type: ignore

"""

EXCEPTION_HANDLERS_FILE = """from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from ._exceptions import ApiError


def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse({"message": exc.get_message()}, status_code=exc.status_code)


def set_api_error_handler(app: FastAPI):
    app.add_exception_handler(ApiError, api_error_handler)

"""

EXCEPTIONS_FILE = """from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class EnvironmentNotSet(Exception):
    def __init__(self, key: str) -> None:
        self.key = key

    def __str__(self) -> str:
        return f"The env key {{self.key}} is unset"


class ApiError(Exception):

    status_code = HTTP_400_BAD_REQUEST

    __msg: str

    def get_message(self) -> str:
        try:
            return self.__msg
        except AttributeError:
            return "An error occurred"

    def set_msg(self, msg: str):
        self.__msg = msg

    @classmethod
    def from_message(cls, message: str, status_code: int = None):
        exc = cls()
        exc.set_msg(message)
        exc.status_code = status_code or cls.status_code
        return exc


class RepositoryError(ApiError):
    _object: str

    @classmethod
    def preload_cls(cls, obj: str = "Object"):
        exc = cls()
        exc._object = obj
        return exc


class DoesNotExist(RepositoryError):
    status_code = HTTP_404_NOT_FOUND

    def get_message(self) -> str:
        return f"{{self._object}} not found"


class AlreadyExists(RepositoryError):
    def get_message(self) -> str:
        return f"{{self._object}} already exists"


class UnexpectedError(ApiError):
    def __init__(self) -> None:
        pass

    status_code = HTTP_500_INTERNAL_SERVER_ERROR

    def get_message(self) -> str:
        return "An unexpected error occured, talk to the tech team"


class UnAuthorizedError(ApiError):
    def __init__(self) -> None:
        pass

    status_code = HTTP_403_FORBIDDEN

    def get_message(self) -> str:
        return "You do not have permission to use this route"

"""

DUNDER_EXC = """from ._exception_handlers import set_api_error_handler
from ._exceptions import (
    EnvironmentNotSet,
    ApiError,
    RepositoryError,
    DoesNotExist,
    AlreadyExists,
    UnexpectedError,
    UnAuthorizedError,
)

__all__ = [
    "set_api_error_handler",
    "EnvironmentNotSet",
    "ApiError",
    "RepositoryError",
    "DoesNotExist",
    "AlreadyExists",
    "UnexpectedError",
    "UnAuthorizedError",
]

"""

TEST_UTILS = """import io
import logging
import os
from unittest.mock import patch

import pytest
from {project_folder}.{exceptions_folder} import EnvironmentNotSet
from {project_folder} import {utils_folder}


def get_logger(string_stream: io.StringIO) -> logging.Logger:
    handler = logging.StreamHandler(string_stream)
    logger = logging.getLogger("test.log")
    logger.setLevel(logging.INFO)
    for handler in logger.handlers:
        logger.removeHandler(handler)
    logger.addHandler(handler)
    return logger


def get_required(environment: env.Environment):
    env_type = environment.get("ENV", dev="dev", parser=env.Env)
    return environment.required_if(env_type == env.Env.PROD)


@patch.dict(os.environ, {}, clear=True)
def test_get_returns_default():
    string_stream = io.StringIO("")
    logger = get_logger(string_stream)
    environment = env.Environment(logger)
    response = environment.get("TEST_KEY", dev="231", parser=int)
    assert isinstance(response, int)
    assert response == 231


@patch.dict(os.environ, {}, clear=True)
def test_get_sends_warning_log_on_prod(caplog):
    string_stream = io.StringIO("")
    logger = get_logger(string_stream)
    caplog.clear()
    environment = env.Environment(logger)
    environment.get("TEST_KEY", dev="231", parser=int)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == logging.getLevelName(logging.WARNING)


@patch.dict(os.environ, {"TEST_KEY": "123"}, clear=True)
def test_required_returns_value_on_dev():
    string_stream = io.StringIO("")
    logger = get_logger(string_stream)
    environment = env.Environment(logger)
    required = get_required(environment)
    response = required("TEST_KEY", dev="123", parser=int)
    assert response == 123


@patch.dict(os.environ, {"ENV": "prod"}, clear=True)
def test_required_raises_environment_not_set_on_prod():
    environment = env.Environment()
    required = get_required(environment)
    with pytest.raises(EnvironmentNotSet) as exc_info:
        required("TEST_KEY", dev="123", parser=int)
    assert str(exc_info.value) == "The key: TEST_KEY is not set."


@patch.dict(os.environ, {"TEST_KEY": "123"}, clear=True)
def test_get_return_parsed():
    environment = env.Environment()
    response = environment.get("TEST_KEY", dev="123")
    assert isinstance(response, str)
    assert response == os.environ["TEST_KEY"]


@patch.dict(os.environ, {"TEST_KEY": "123"}, clear=True)
def test_set_logger_sets_logger():
    string_stream = io.StringIO("")
    logger = get_logger(string_stream)
    environment = env.Environment()
    environment.set_logger(logger)
    assert environment.logger == logger

"""


MAIN_FILE = """from fastapi import FastAPI

from {project_folder} import routes
from {project_folder}.{providers_folder} import DatabaseProvider, HttpProvider
from {project_folder}.{exceptions_folder} import set_api_error_handler

def create_startup_handler(_app: FastAPI):
    def _startup():
        _app.state.database_provider = DatabaseProvider()
        _app.state.http_provider = HttpProvider()

    return _startup


def create_shutdown_handler(_app: FastAPI):
    async def _shutdown():
        await _app.state.http_provider.finish()

    return _shutdown


def get_application(prefix: str = ""):
    _app = FastAPI(
        title="{project_as_title}",
        openapi_url=f"{{prefix}}/openapi.json",
        docs_url=f"{{prefix}}/docs",
        redoc_url=f"{{prefix}}/redoc",
    )
    _app.include_router(routes.router, prefix=f"{{prefix}}")

    _app.add_event_handler("startup", create_startup_handler(_app))
    _app.add_event_handler("shutdown", create_shutdown_handler(_app))
    set_api_error_handler(_app)

    return _app


app = get_application()


def main():
    import uvicorn

    uvicorn.run("{project_folder}.main:app", reload=True)

"""

GITIGNORE_FILE = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
coverage_html_repor
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

"""


DOCKERFILE = """FROM python:3.9-slim

COPY . /var/www/app

WORKDIR /var/www/app

RUN python3.9 -m pip install -U pip poetry

RUN poetry install --no-dev

EXPOSE 8000

ENTRYPOINT poetry run circusd ./circus.ini --log-level info

"""

PYLINTRC = """[MASTER]

# A comma-separated list of package or module names from where C extensions may
# be loaded. Extensions are loading into the active Python interpreter and may
# run arbitrary code.
extension-pkg-allow-list=

# A comma-separated list of package or module names from where C extensions may
# be loaded. Extensions are loading into the active Python interpreter and may
# run arbitrary code. (This is an alternative name to extension-pkg-allow-list
# for backward compatibility.)
extension-pkg-whitelist=

# Specify a score threshold to be exceeded before program exits with error.
fail-under=10.0

# Files or directories to be skipped. They should be base names, not paths.
ignore=CVS

# Files or directories matching the regex patterns are skipped. The regex
# matches against base names, not paths.
ignore-patterns=env.py, *.pyi

# Python code to execute, usually for sys.path manipulation such as
# pygtk.require().
; init-hook="from pylint.config import find_pylintrc; import os, sys; sys.path.append(os.path.join(os.path.dirname(find_pylintrc())))"

# Use multiple processes to speed up Pylint. Specifying 0 will auto-detect the
# number of processors available to use.
jobs=1

# Control the amount of potential inferred values when inferring a single
# object. This can help the performance when dealing with large functions or
# complex, nested conditions.
limit-inference-results=100

# List of plugins (as comma separated values of python module names) to load,
# usually to register additional checkers.
load-plugins=

# Pickle collected data for later comparisons.
persistent=yes

# When enabled, pylint would attempt to guess common misconfiguration and emit
# user-friendly hints instead of false-positive error messages.
suggestion-mode=yes

# Allow loading of arbitrary C extensions. Extensions are imported into the
# active Python interpreter and may run arbitrary code.
unsafe-load-any-extension=no


[MESSAGES CONTROL]

# Only show warnings with the listed confidence levels. Leave empty to show
# all. Valid levels: HIGH, INFERENCE, INFERENCE_FAILURE, UNDEFINED.
confidence=

# Disable the message, report, category or checker with the given id(s). You
# can either give multiple identifiers separated by comma (,) or put this
# option multiple times (only on the command line, not in the configuration
# file where it should appear only once). You can also use "--disable=all" to
# disable everything first and then reenable specific checks. For example, if
# you want to run only the similarities checker, you can use "--disable=all
# --enable=similarities". If you want to run only the classes checker, but have
# no Warning level messages displayed, use "--disable=all --enable=classes
# --disable=W".
disable=parameter-unpacking,
        unpacking-in-except,
        old-raise-syntax,
        backtick,
        long-suffix,
        old-ne-operator,
        old-octal-literal,
        import-star-module-level,
        non-ascii-bytes-literal,
        raw-checker-failed,
        bad-inline-option,
        locally-disabled,
        file-ignored,
        suppressed-message,
        useless-suppression,
        deprecated-pragma,
        use-symbolic-message-instead,
        apply-builtin,
        basestring-builtin,
        buffer-builtin,
        cmp-builtin,
        coerce-builtin,
        execfile-builtin,
        file-builtin,
        long-builtin,
        raw_input-builtin,
        reduce-builtin,
        standarderror-builtin,
        unicode-builtin,
        xrange-builtin,
        coerce-method,
        delslice-method,
        getslice-method,
        setslice-method,
        no-absolute-import,
        old-division,
        dict-iter-method,
        dict-view-method,
        next-method-called,
        metaclass-assignment,
        indexing-exception,
        raising-string,
        reload-builtin,
        oct-method,
        hex-method,
        nonzero-method,
        cmp-method,
        input-builtin,
        round-builtin,
        intern-builtin,
        unichr-builtin,
        map-builtin-not-iterating,
        zip-builtin-not-iterating,
        range-builtin-not-iterating,
        filter-builtin-not-iterating,
        using-cmp-argument,
        eq-without-hash,
        div-method,
        idiv-method,
        rdiv-method,
        exception-message-attribute,
        invalid-str-codec,
        sys-max-int,
        bad-python3-import,
        deprecated-string-function,
        deprecated-str-translate-call,
        deprecated-itertools-function,
        deprecated-types-field,
        next-method-defined,
        dict-items-not-iterating,
        dict-keys-not-iterating,
        dict-values-not-iterating,
        deprecated-operator-function,
        deprecated-urllib-function,
        xreadlines-attribute,
        deprecated-sys-function,
        exception-escape,
        comprehension-escape,
        missing-docstring,
        import-outside-toplevel,
        unused-import,
        no-name-in-module,
        no-member,
        super-init-not-called

# Enable the message, report, category or checker with the given id(s). You can
# either give multiple identifier separated by comma (,) or put this option
# multiple time (only on the command line, not in the configuration file where
# it should appear only once). See also the "--disable" option for examples.
enable=c-extension-no-member


[REPORTS]

# Python expression which should return a score less than or equal to 10. You
# have access to the variables 'error', 'warning', 'refactor', and 'convention'
# which contain the number of messages in each category, as well as 'statement'
# which is the total number of statements analyzed. This score is used by the
# global evaluation report (RP0004).
evaluation=10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)

# Template used to display messages. This is a python new-style format string
# used to format the message information. See doc for all details.
#msg-template=

# Set the output format. Available formats are text, parseable, colorized, json
# and msvs (visual studio). You can also give a reporter class, e.g.
# mypackage.mymodule.MyReporterClass.
output-format=text

# Tells whether to display a full report or only the messages.
reports=no

# Activate the evaluation score.
score=yes


[REFACTORING]

# Maximum number of nested blocks for function / method body
max-nested-blocks=2

# Complete name of functions that never returns. When checking for
# inconsistent-return-statements if a never returning function is called then
# it will be considered as an explicit return statement and no message will be
# printed.
never-returning-functions=sys.exit,argparse.parse_error


[SIMILARITIES]

# Ignore comments when computing similarities.
ignore-comments=yes

# Ignore docstrings when computing similarities.
ignore-docstrings=yes

# Ignore imports when computing similarities.
ignore-imports=no

# Minimum lines number of a similarity.
min-similarity-lines=3


[LOGGING]

# The type of string formatting that logging methods do. `old` means using %
# formatting, `new` is for `{}` formatting.
logging-format-style=old

# Logging modules to check that the string format arguments are in logging
# function parameter format.
logging-modules=logging


[BASIC]

# Naming style matching correct argument names.
argument-naming-style=snake_case

# Regular expression matching correct argument names. Overrides argument-
# naming-style.
#argument-rgx=

# Naming style matching correct attribute names.
attr-naming-style=snake_case

# Regular expression matching correct attribute names. Overrides attr-naming-
# style.
#attr-rgx=

# Bad variable names which should always be refused, separated by a comma.
bad-names=foo,
          bar,
          baz,
          toto,
          tutu,
          tata

# Bad variable names regexes, separated by a comma. If names match any regex,
# they will always be refused
bad-names-rgxs=

# Naming style matching correct class attribute names.
class-attribute-naming-style=any

# Regular expression matching correct class attribute names. Overrides class-
# attribute-naming-style.
#class-attribute-rgx=

# Naming style matching correct class constant names.
class-const-naming-style=UPPER_CASE

# Regular expression matching correct class constant names. Overrides class-
# const-naming-style.
#class-const-rgx=

# Naming style matching correct class names.
class-naming-style=PascalCase

# Regular expression matching correct class names. Overrides class-naming-
# style.
#class-rgx=

# Naming style matching correct constant names.
const-naming-style=UPPER_CASE

# Regular expression matching correct constant names. Overrides const-naming-
# style.
#const-rgx=

# Minimum line length for functions/classes that require docstrings, shorter
# ones are exempt.
docstring-min-length=-1

# Naming style matching correct function names.
function-naming-style=snake_case

# Regular expression matching correct function names. Overrides function-
# naming-style.
#function-rgx=

# Good variable names which should always be accepted, separated by a comma.
good-names=i,
           j,
           k,
           ex,
           Run,
           _

# Good variable names regexes, separated by a comma. If names match any regex,
# they will always be accepted
good-names-rgxs=

# Include a hint for the correct naming format with invalid-name.
include-naming-hint=yes

# Naming style matching correct inline iteration names.
inlinevar-naming-style=any

# Regular expression matching correct inline iteration names. Overrides
# inlinevar-naming-style.
#inlinevar-rgx=

# Naming style matching correct method names.
method-naming-style=snake_case

# Regular expression matching correct method names. Overrides method-naming-
# style.
#method-rgx=

# Naming style matching correct module names.
module-naming-style=snake_case

# Regular expression matching correct module names. Overrides module-naming-
# style.
#module-rgx=

# Colon-delimited sets of names that determine each other's naming style when
# the name regexes allow several styles.
name-group=

# Regular expression which should only match function or class names that do
# not require a docstring.
no-docstring-rgx=^_

# List of decorators that produce properties, such as abc.abstractproperty. Add
# to this list to register other decorators that produce valid properties.
# These decorators are taken in consideration only for invalid-name.
property-classes=abc.abstractproperty

# Naming style matching correct variable names.
variable-naming-style=snake_case

# Regular expression matching correct variable names. Overrides variable-
# naming-style.
#variable-rgx=


[STRING]

# This flag controls whether inconsistent-quotes generates a warning when the
# character used as a quote delimiter is used inconsistently within a module.
check-quote-consistency=yes

# This flag controls whether the implicit-str-concat should generate a warning
# on implicit string concatenation in sequences defined over several lines.
check-str-concat-over-line-jumps=no


[TYPECHECK]

# List of decorators that produce context managers, such as
# contextlib.contextmanager. Add to this list to register other decorators that
# produce valid context managers.
contextmanager-decorators=contextlib.contextmanager

# List of members which are set dynamically and missed by pylint inference
# system, and so shouldn't trigger E1101 when accessed. Python regular
# expressions are accepted.
generated-members=

# Tells whether missing members accessed in mixin class should be ignored. A
# mixin class is detected if its name ends with "mixin" (case insensitive).
ignore-mixin-members=yes

# Tells whether to warn about missing members when the owner of the attribute
# is inferred to be None.
ignore-none=yes

# This flag controls whether pylint should warn about no-member and similar
# checks whenever an opaque object is returned when inferring. The inference
# can return multiple potential results while evaluating a Python object, but
# some branches might not be evaluated, which results in partial inference. In
# that case, it might be useful to still emit no-member and other checks for
# the rest of the inferred objects.
ignore-on-opaque-inference=yes

# List of class names for which member attributes should not be checked (useful
# for classes with dynamically set attributes). This supports the use of
# qualified names.
ignored-classes=optparse.Values,thread._local,_thread._local

# List of module names for which member attributes should not be checked
# (useful for modules/projects where namespaces are manipulated during runtime
# and thus existing member attributes cannot be deduced by static analysis). It
# supports qualified module names, as well as Unix pattern matching.
ignored-modules=

# Show a hint with possible names when a member name was not found. The aspect
# of finding the hint is based on edit distance.
missing-member-hint=yes

# The minimum edit distance a name should have in order to be considered a
# similar match for a missing member name.
missing-member-hint-distance=1

# The total number of similar names that should be taken in consideration when
# showing a hint for a missing member.
missing-member-max-choices=1

# List of decorators that change the signature of a decorated function.
signature-mutators=


[MISCELLANEOUS]

# List of note tags to take in consideration, separated by a comma.
notes=FIXME,
      XXX,
      TODO

# Regular expression of note tags to take in consideration.
#notes-rgx=


[FORMAT]

# Expected format of line ending, e.g. empty (any line ending), LF or CRLF.
expected-line-ending-format=

# Regexp for a line that is allowed to be longer than the limit.
ignore-long-lines=^\s*(# )?<?https?://\S+>?$

# Number of spaces of indent required inside a hanging or continued line.
indent-after-paren=4

# String used as indentation unit. This is usually "    " (4 spaces) or "\t" (1
# tab).
indent-string='    '

# Maximum number of characters on a single line.
max-line-length=100

# Maximum number of lines in a module.
max-module-lines=1000

# Allow the body of a class to be on the same line as the declaration if body
# contains single statement.
single-line-class-stmt=no

# Allow the body of an if to be on the same line as the test if there is no
# else.
single-line-if-stmt=no


[VARIABLES]

# List of additional names supposed to be defined in builtins. Remember that
# you should avoid defining new builtins when possible.
additional-builtins=

# Tells whether unused global variables should be treated as a violation.
allow-global-unused-variables=yes

# List of names allowed to shadow builtins
allowed-redefined-builtins=

# List of strings which can identify a callback function by name. A callback
# name must start or end with one of those strings.
callbacks=cb_,
          _cb

# A regular expression matching the name of dummy variables (i.e. expected to
# not be used).
dummy-variables-rgx=_+$|(_[a-zA-Z0-9_]*[a-zA-Z0-9]+?$)|dummy|^ignored_|^unused_

# Argument names that match this expression will be ignored. Default to name
# with leading underscore.
ignored-argument-names=_.*|^ignored_|^unused_

# Tells whether we should check for unused import in __init__ files.
init-import=no

# List of qualified module names which can have objects that can redefine
# builtins.
redefining-builtins-modules=six.moves,past.builtins,future.builtins,builtins,io


[SPELLING]

# Limits count of emitted suggestions for spelling mistakes.
max-spelling-suggestions=4

# Spelling dictionary name. Available dictionaries: none. To make it work,
# install the 'python-enchant' package.
spelling-dict=

# List of comma separated words that should be considered directives if they
# appear and the beginning of a comment and should not be checked.
spelling-ignore-comment-directives=fmt: on,fmt: off,noqa:,noqa,nosec,isort:skip,mypy:

# List of comma separated words that should not be checked.
spelling-ignore-words=

# A path to a file that contains the private dictionary; one word per line.
spelling-private-dict-file=

# Tells whether to store unknown words to the private dictionary (see the
# --spelling-private-dict-file option) instead of raising a message.
spelling-store-unknown-words=no


[CLASSES]

# Warn about protected attribute access inside special methods
check-protected-access-in-special-methods=yes

# List of method names used to declare (i.e. assign) instance attributes.
defining-attr-methods=__init__,
                      __new__,
                      setUp,
                      __post_init__

# List of member names, which should be excluded from the protected access
# warning.
exclude-protected=_asdict,
                  _fields,
                  _replace,
                  _source,
                  _make

# List of valid names for the first argument in a class method.
valid-classmethod-first-arg=cls

# List of valid names for the first argument in a metaclass class method.
valid-metaclass-classmethod-first-arg=metacls


[DESIGN]

# Maximum number of arguments for function / method.
max-args=4

# Maximum number of attributes for a class (see R0902).
max-attributes=7

# Maximum number of boolean expressions in an if statement (see R0916).
max-bool-expr=5

# Maximum number of branch for function / method body.
max-branches=4

# Maximum number of locals for function / method body.
max-locals=15

# Maximum number of parents for a class (see R0901).
max-parents=7

# Maximum number of public methods for a class (see R0904).
max-public-methods=20

# Maximum number of return / yield for function / method body.
max-returns=6

# Maximum number of statements in function / method body.
max-statements=50

# Minimum number of public methods for a class (see R0903).
min-public-methods=0


[IMPORTS]

# List of modules that can be imported at any level, not just the top level
# one.
allow-any-import-level=

# Allow wildcard imports from modules that define __all__.
allow-wildcard-with-all=no

# Analyse import fallback blocks. This can be used to support both Python 2 and
# 3 compatible code, which means that the block might have code that exists
# only in one or another interpreter, leading to false positives when analysed.
analyse-fallback-blocks=no

# Deprecated modules which should not be used, separated by a comma.
deprecated-modules=optparse,tkinter.tix

# Output a graph (.gv or any supported image format) of external dependencies
# to the given file (report RP0402 must not be disabled).
ext-import-graph=

# Output a graph (.gv or any supported image format) of all (i.e. internal and
# external) dependencies to the given file (report RP0402 must not be
# disabled).
import-graph=

# Output a graph (.gv or any supported image format) of internal dependencies
# to the given file (report RP0402 must not be disabled).
int-import-graph=

# Force import order to recognize a module as part of the standard
# compatibility libraries.
known-standard-library=

# Force import order to recognize a module as part of a third party library.
known-third-party=enchant

# Couples of modules and preferred modules, separated by a comma.
preferred-modules=


[EXCEPTIONS]

# Exceptions that will emit a warning when being caught. Defaults to
# "BaseException, Exception".
overgeneral-exceptions=BaseException,
                       Exception

"""

CIRCUS_INI = """[circus]
check_delay = 5

[watcher:gunicorn]
cmd = gunicorn
args = --workers 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --name {project_name} --log-level=info {project_folder}.main:application
numprocesses = 1
working_dir = .
autostart = true
max_retry = -1
priority = 500
copy_env = true
"""

COVERAGE_RC = """# .coveragerc to control coverage.py
[run]
source = {project_folder}
omit=**/settings.py

[report]
# Regexes for lines to exclude from consideration
exclude_lines =
    # Have to re-enable the standard pragma
    pragma: no cover

    # Don't complain about missing debug-only code:
    def __repr__
    if self\.debug

    # Don't complain if tests don't hit defensive assertion code:
    raise AssertionError
    raise NotImplementedError

    # Don't complain if non-runnable code isn't run:
    if 0:
    if __name__ == .__main__.:
    
    # Don't complain about pass statements:
    pass
ignore_errors = True

[html]
directory = coverage_html_repor

"""

MODEL_FINDER_FILE = """import importlib
import inspect
from pathlib import Path
from typing import Optional

from sqlalchemy import Table


class ModelFinder:
    def __init__(self, path: Path, root: Path = None):
        self.path = path
        self.models = {}
        self.root = root or path

    def find(self):
        if self.path.is_dir():
            self.find_from_dir()
        else:
            self.find_from_file()

    def find_from_dir(self, path: Optional[Path] = None):
        if path is None:
            path = self.path
        if "pycache" in path.name or ".pyc" in path.name:
            return
        for item in path.iterdir():
            if item.is_dir():
                self.find_from_dir(item)
                continue
            if ".py" in path.name and "__init__.py" != path.name:
                continue
            self.find_from_file(item)

    def find_from_file(self, path: Optional[Path] = None):
        if path is None:
            path = self.path
        if not path.is_file():
            return
        mod = importlib.import_module(self.get_import(path))
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj):
                if issubclass(obj, Table) and name != "Table":
                    self.models[name] = obj

    def get_import(self, target: Path):
        target_str = str(target)
        result = target_str[target_str.index(self.root.name):].replace("/", ".").replace(".py", "")
        return result

    def __getitem__(self, name: str) -> Table:
        if self.models.get(name):
            return self.models[name]
        raise KeyError(name)


"""

METADATA_FILE = """from sqlalchemy import MetaData

metadata = MetaData()

"""

DATABASE_MAIN_FILE = """from {project_folder}.{core_folder}.settings import BASE_DIR
from ._model_finder import ModelFinder
from .metadata import metadata


def preload():
    model_finder = ModelFinder(BASE_DIR /"database" / "tables", BASE_DIR)
    model_finder.find()

def get_metadata():
    preload()
    return metadata
"""

DATABASE_FILTERS = """from abc import abstractmethod
import operator
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union

from sqlalchemy import Column, Table, and_, false, or_, true, Boolean, DateTime
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.elements import BooleanClauseList


class Filter:
    def where(self, table: Table):
        pass

    @abstractmethod
    def __bool__(self):
        ...


class CompareOptions(str, Enum):
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER = "gt"
    GREATER_EQUAL = "ge"
    LESSER = "lt"
    LESSER_EQUAL = "le"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    NULL = "null"


@dataclass
class FieldFilter(Filter):
    field: str
    value: Optional[Any]
    comparison: CompareOptions = CompareOptions.EQUAL
    enum_value: bool = False
    sql_func: Optional[Callable[[Column], Any]] = None

    def __eq__(self, filter: Filter) -> bool:
        if not isinstance(filter, type(self)):
            return False
        return (self.field, self.value, self.comparison) == (
            filter.field,
            filter.value,
            filter.comparison,
        )

    def __post_init__(self):
        if isinstance(self.value, bool) and self.comparison is not CompareOptions.NULL:
            self.value = true() if self.value else false()
        if isinstance(self.value, Enum):
            if self.enum_value:
                self.value = self.value and self.value.value
            else:
                self.value = self.value and self.value.name

    def where(self, table: Table):
        return self.attr(table)  # type: ignore

    def attr(self, table: Table):
        attr = self._attr(table, self.field)
        if not self:
            return True
        if self.sql_func:
            attr = self.sql_func(attr)  # type: ignore
        if self.comparison not in [
            CompareOptions.CONTAINS,
            CompareOptions.ICONTAINS,
            CompareOptions.NULL,
        ]:
            return getattr(operator, self.comparison.value)(attr, self.value)
        if self.comparison == CompareOptions.NULL:
            return attr.is_(None) if self.value else attr.is_not(None)
        if self.comparison == CompareOptions.CONTAINS:
            return attr.like(f"%{self.value}%")
        return attr.ilike(f"%{self.value}%")

    @staticmethod
    def _attr(table: Table, field: str) -> Union[Column, RelationshipProperty]:
        result = getattr(table.c, field, None)
        if result is None:
            raise NotImplementedError
        return result

    def __bool__(self):
        return self.value is not None


@dataclass(init=False)
class FilterJoins(Filter):
    operator: type[BooleanClauseList]
    filters: tuple[Filter, ...]

    def __init__(self, *filters: Filter) -> None:
        self.filters = filters

    def where(self, table: Table):
        return self.operator(*(f.where(table) for f in self.filters))

    def __bool__(self):
        return True


class OrFilter(FilterJoins):
    @property
    def operator(self):
        return or_


class AndFilter(FilterJoins):
    @property
    def operator(self):
        return and_

"""

DATABASE_HELPERS_FILE = """from typing import TypeVar, Callable

from sqlalchemy import Column, func
from sqlalchemy.engine import Row

from {project_folder}.dtos.base import DTO
from {project_folder} import providers, exc


DTO_T = TypeVar("DTO_T", bound=DTO)


def to_dto(klass: type[DTO_T]) -> Callable[[Row], DTO_T]:
    def _to_dto(item: Row):
        return klass.parse_obj(dict(item))

    return _to_dto



def day(column: Column):
    return func.day(column)


def month(column: Column):
    return func.month(column)


async def get(
    database_provider: providers.DatabaseProvider, table: Table, **where
) -> Optional[Row]:
    async with database_provider.begin() as conn:
        result = await conn.execute(
            table.select().where(
                *(getattr(table, key) == value for key, value in where)
            )
        )
        return result.first()


async def get_or_raise(
    database_provider: providers.DatabaseProvider, table: Table, **where
) -> dict:
    result = await get(database_provider, table, **where)
    if not result:
        raise exc.DoesNotExist
    return dict(result)


def sync_get(
    database_provider: providers.DatabaseProvider, table: Table, **where
) -> Optional[Row]:
    with database_provider.sync() as conn:
        result = conn.execute(
            table.select().where(
                *(getattr(table, key) == value for key, value in where)
            )
        )
        return result.first()


def sync_get_or_raise(
    database_provider: providers.DatabaseProvider, table: Table, **where
) -> dict:
    result = sync_get(database_provider, table, **where)
    if not result:
        raise exc.DoesNotExist
    return dict(result)

class Repository:
    pass

"""


ALEMBIC_README = """Generic single-database configuration."""

SCRIPT_PY_MAKO = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
'''

ALEMBIC_ENV = '''# type: ignore

from logging.config import fileConfig

from alembic import context
from {project_folder}.{providers_folder} import DatabaseProvider, DriverTypes
from {project_folder}.{database_folder}.main import get_metadata
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = get_metadata()

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = DatabaseProvider.get_driver_conn_uri(DriverTypes.{db_type}, False)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    cfg = config.get_section(config.config_ini_section)
    cfg["sqlalchemy.url"] = DatabaseProvider.get_driver_conn_uri(DriverTypes.{db_type}, False)
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

ALEMBIC_INI = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = ./{alembic_folder}

# template used to generate migration files
# file_template = %(rev)s_%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
; prepend_sys_path = ./app

# timezone to use when rendering the date
# within the migration file as well as the filename.
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; this defaults
# to ./alemibc/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path
# version_locations = %(here)s/bar %(here)s/bat ./alemibc/versions

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

DOTENV = """ENV=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
"""


TABLE_TEMPLATE = """from sqlalchemy import Table, Column, Integer
from {project_folder}.database.metadata import metadata

# Add your table columns here

{table_normalized_name} = Table(
    "{table_name}", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True)
)

"""

DUNDER_IMPORT_TEMPLATE = """from .{file} import {public_name}"""

DUNDER_TEMPLATE = """{imports}

__all__ = [{classes}]
"""

ENUM_AUTO_OPTS_TEMPLATE = "{opt} = {idx}"

ENUM_TEMPLATE = '''from enum import Enum

# Add your enum choices here


class {enum_name}(Enum):
    """ Representation of {enum_name} """
    
    {auto_opts}
'''

DTO_TEMPLATE = '''from {project_folder}.dtos.base import DTO

# Add your dto fields here

class {dto_name}(DTO):
    """ Representation of {dto_name} """
    

'''

ASYNC_REPOSITORY_BOILERPLATE = """from {project_folder} import exc, providers
from sqlalchemy.exc import IntegrityError
from {project_folder}.database import helpers, filters
from {project_folder}.database.tables.{module_name} import {table_name}
from {project_folder}.dtos import {module_name}


class {entity_name}Repository(helpers.Repository):
    def __init__(self, database_provider: providers.DatabaseProvider) -> None:
        self.database_provider = database_provider

    async def create(self, payload: \"{module_name}.{entity_name}In\") -> None:
        query = {table_name}.insert().values(payload.dict())
        async with self.database_provider.begin() as conn:
            try:
                await conn.execute(query)
            except IntegrityError as err:
                raise exc.AlreadyExists from err

    async def get(self, id: int):
        return await helpers.get_or_raise(self.database_provider, {table_name}, id=id)

    async def list(self, *where: filters.Filter):
        query = {table_name}.select().where(*(f.where({table_name}) for f in where))
        async with self.database_provider.begin() as conn:
            result = await conn.execute(query)
            return {{"data": list(map(dict, result.all()))}}

    async def update(self, id: int, payload: \"{module_name}.{entity_name}Edit\"):
        await helpers.get_or_raise(self.database_provider, {table_name}, id=id)
        query = {table_name}.update().values(payload.dict()).where({table_name}.c.id == id)
        async with self.database_provider.begin() as conn:
            await conn.execute(query)

    async def delete(self, id: int):
        await helpers.get_or_raise(self.database_provider, {table_name}, id=id)
        query = {table_name}.delete().where({table_name}.c.id == id)
        async with self.database_provider.begin() as conn:
            await conn.execute(query)
"""

SYNC_REPOSITORY_BOILERPLATE = """from {project_folder} import exc, providers
from sqlalchemy.exc import IntegrityError
from {project_folder}.database import helpers, filters
from {project_folder}.database.tables.{module_name} import {table_name}
from {project_folder}.dtos import {module_name}


class {entity_name}Repository(helpers.Repository):
    def __init__(self, database_provider: providers.DatabaseProvider) -> None:
        self.database_provider = database_provider

    def create(self, payload: \"{module_name}.{entity_name}In\") -> None:
        query = {table_name}.insert().values(payload.dict())
        with self.database_provider.sync() as conn:
            try:
                conn.execute(query)
            except IntegrityError as err:
                raise exc.AlreadyExists from err

    def get(self, id: int):
        return helpers.sync_get_or_raise(self.database_provider, {table_name}, id=id)

    def list(self, *where: filters.Filter):
        query = {table_name}.select().where(*(f.where({table_name}) for f in where))
        with self.database_provider.sync() as conn:
            result = conn.execute(query)
            return {{"data": list(map(dict, result.all()))}}

    def update(self, id: int, payload: \"{module_name}.{entity_name}Edit\"):
        helpers.sync_get_or_raise(self.database_provider, {table_name}, id=id)
        query = {table_name}.update().values(payload.dict()).where({table_name}.c.id == id)
        with self.database_provider.sync() as conn:
            conn.execute(query)

    def delete(self, id: int):
        helpers.sync_get_or_raise(self.database_provider, {table_name}, id=id)
        query = {table_name}.delete().where({table_name}.c.id == id)
        with self.database_provider.sync() as conn:
            conn.execute(query)

"""


ASYNC_ROUTE_BOILERPLATE = """
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status
from {project_folder}.database.repositories import {entity_name}Repository
from {project_folder}.dtos import {module_name}
from {project_folder}.routes import dependencies
from {project_folder} import providers


{entity_lower}_router = APIRouter(prefix="/{entity_lower}")


@{entity_lower}_router.get("/{{id}}/", response_model={module_name}.{entity_name})
async def get_{entity_lower}(
    id: int = Path(...),
    database_provider: providers.DatabaseProvider = Depends(
        dependencies.get_database_provider
    ),
):
    return await {entity_name}Repository(database_provider).get(id)


@{entity_lower}_router.get("/", response_model={module_name}.{entity_name}EmbedArray)
async def list_{entity_lower}s(
    database_provider: providers.DatabaseProvider = Depends(
        dependencies.get_database_provider
    ),
):  # add filters as query
    return await {entity_name}Repository(database_provider).list()

@{entity_lower}_router.post("/")
async def create_{entity_lower}(payload: {module_name}.{entity_name}In, database_provider: providers.DatabaseProvider = Depends(dependencies.get_database_provider)):
    await {entity_name}Repository(database_provider).create(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@{entity_lower}_router.put("/{{id}}/")
async def edit_{entity_lower}(id: int = Path(...), payload: {module_name}.{entity_name}Edit = Body(...), database_provider: providers.DatabaseProvider = Depends(dependencies.get_database_provider)):
    await {entity_name}Repository(database_provider).update(id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@{entity_lower}_router.delete("/{{id}}/")
async def delete_{entity_lower}(
    id: int = Path(...),
    database_provider: providers.DatabaseProvider = Depends(
        dependencies.get_database_provider
    ),
):
    await {entity_name}Repository(database_provider).delete(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""

SYNC_ROUTE_BOILERPLATE = """
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status
from {project_folder}.database.repositories import {entity_name}Repository
from {project_folder}.dtos import {module_name}
from {project_folder}.routes import dependencies
from {project_folder} import providers


{entity_lower}_router = APIRouter(prefix="/{entity_lower}")

@{entity_lower}_router.get("/{{id}}/", response_model={module_name}.{entity_name})
def get_{entity_lower}(
    id: int = Path(...),
    database_provider: providers.DatabaseProvider = Depends(
        dependencies.get_database_provider
    ),
):
    return {entity_name}Repository(database_provider).get(id)


@{entity_lower}_router.get("/", response_model={module_name}.{entity_name}EmbedArray)
def list_{entity_lower}s(
    database_provider: providers.DatabaseProvider = Depends(
        dependencies.get_database_provider
    ),
):  # add filters as query
    return {entity_name}Repository(database_provider).list()

@{entity_lower}_router.post("/")
def create_{entity_lower}(payload: {module_name}.{entity_name}In, database_provider: providers.DatabaseProvider = Depends(dependencies.get_database_provider)):
    {entity_name}Repository(database_provider).create(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@{entity_lower}_router.put("/{{id}}/")
def edit_{entity_lower}(id: int = Path(...), payload: {module_name}.UserEdit = Body(...), database_provider: providers.DatabaseProvider = Depends(dependencies.get_database_provider)):
    {entity_name}Repository(database_provider).update(id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@{entity_lower}_router.delete("/{{id}}/")
def delete_{entity_lower}(
    id: int = Path(...),
    database_provider: providers.DatabaseProvider = Depends(
        dependencies.get_database_provider
    ),
):
    {entity_name}Repository(database_provider).delete(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
"""

BASE_EMBED_ARRAY_BOILERPLATE = """from {project_folder}.dtos.base import embed_array
from ._{entity_lower} import {entity_name}


{entity_name}EmbedArray = embed_array({entity_name}, __name__)
"""