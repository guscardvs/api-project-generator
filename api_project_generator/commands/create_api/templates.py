from jinja2 import Template

from api_project_generator.helpers.utils import lead_spaces_as_tabs

BASE_TEST_FILE = Template(
    """from {{project_folder}} import __version__

def test_{{project_folder}}():
    assert __version__ == "{{version}}"

"""
)

SETTINGS_FILE = Template(
    """
from pathlib import Path

from {{project_folder}}.core.log import set_logger
from gyver.config import (
    EnvConfig, 
    Env, 
    DotFile, 
    AdapterConfigFactory
)
{% if db %}
from gyver.database import DatabaseConfig, Driver
{% endif %}

BASE_DIR = Path(__file__).resolve().parent.parent
config = EnvConfig(DotFile('.env-local', Env.LOCAL))
logger = set_logger(config.env)
factory = AdapterConfigFactory(config)

{% if db %}
db_config_factory = factory.maker(DatabaseConfig, __prefix__="db", db_driver=Driver.{{driver.name}})
{% endif %}
"""
)

LOG_FILE = """import logging

from gyver.config import Env


def set_logger(env: Env):
    logger = logging.getLogger("uvicorn.error" if env != Env.PRD else "gunicorn.error")
    logger.setLevel(logging.INFO)
    return logger

"""

DUNDER_ROUTES = Template(
    """from .{{main_router_file}} import router


__all__ = ["router"] 
"""
)

MAIN_ROUTER_FILE = """from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def validate_health():
    return "Ok"

"""


DATABASE_API_FILE = """from fastapi import Request, Depends
from typing_extensions import Annotated

from gyver.database import DatabaseAdapter, AsyncSessionContext, SessionContext

def get_database_provider(request: Request) -> DatabaseAdapter:
    return request.app.state.database_provider

def get_async_context(request: Request) -> AsyncSessionContext:
    return get_database_provider(request).async_session()

def get_sync_context(request: Request) -> SessionContext:
    return get_database_provider(request).session()

AsyncContext = Annotated[AsyncSessionContext, Depends(get_async_context)]
SyncContext = Annotated[SessionContext, Depends(get_sync_context)]

"""

BASE_SCHEMA_FILE = """from typing import Generic, TypeVar

from pydantic.generics import GenericModel
from gyver.model import Model

T = TypeVar("T")

class EmbedListSchema(GenericModel, Generic[T], Model):
    data: list[T]
"""

EXCEPTION_HANDLERS_FILE = """from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from .exceptions import ApiError, exception_handler


def set_api_error_handler(app: FastAPI):
    app.add_exception_handler(ApiError, exception_handler)

"""

EXCEPTIONS_FILE = '''from collections.abc import Callable, Coroutine
from functools import wraps
from http import HTTPStatus
from typing import Any, TypeVar, Optional
from typing_extensions import ParamSpec

from fastapi import Request
from fastapi.responses import ORJSONResponse
from gyver.attrs import asdict, mutable
from gyver.model import Model
from pydantic import Field, validator


@mutable(slots=False)
class APIError(Exception):
    """
    Represents an error that occurs in the API.
    """

    message: str
    key: str
    status: HTTPStatus
    field: Optional[str] = None

    def __post_init__(self):
        """
        Initializes the APIError object.
        """
        Exception.__init__(self, self.message, self.key, self.status, self.field)


error_response_status = (404, 409, 400, 401, 403, 422)

as_status = HTTPStatus


def not_found_error(target: str, value: str) -> APIError:
    """
    Returns an APIError object indicating that the specified target was not found.

    :param target: The name of the target that was not found.
    :param value: The value of the target that was not found.
    :return: An APIError object with the appropriate message, key, and status code.
    """
    return APIError(f"{target} was not found", "004", as_status(404), value)


def already_exists_error(target: str, value: str) -> APIError:
    """
    Returns an APIError object indicating that the specified target already exists.

    :param target: The name of the target that already exists.
    :param value: The value of the target that already exists.
    :return: An APIError object with the appropriate message, key, and status code.
    """
    return APIError(f"{target} already exists", "009", as_status(409), value)


def forbidden_error(field: Optional[str], message: str = "Forbidden") -> APIError:
    """
    Returns an APIError object indicating that the request was forbidden.

    :param field: An optional field name that caused the error.
    :return: An APIError object with the appropriate message, key, and status code.
    """
    return APIError(message, "002", as_status(403), field)


def not_authenticated(
    message: str = "Not Authenticated", key_extra: str = "0"
) -> APIError:
    """
    Returns an APIError object indicating that the request could not be authenticated.

    :param message: An optional message to include in the error.
    :param key_extra: An optional extra string to append to the error key.
    :return: An APIError object with the appropriate message, key, and status code.
    """
    return APIError(message, f"001-{key_extra}", as_status(401))


def invalid_or_expired_token() -> APIError:
    """
    Returns an APIError object indicating that the provided token is invalid or has expired.

    :return: An APIError object with the appropriate message, key, and status code.
    """
    return not_authenticated("Invalid or Expired Token", key_extra="1")


def field_error(field: str, format: str, received: str) -> APIError:
    """
    Returns an APIError object indicating that the specified field is invalid.

    :param name: The name of the field that is invalid.
    :param format: The expected format of the field.
    :param received: The received value of the field.
    :return: An APIError object with the appropriate message, key, and status code.
    """
    message = (
        f"Invalid field: {field}. Must be in {format} format. Received {received}."
    )
    return APIError(message, "003", as_status(422), field)


def unexpected_error(reason: str):
    """
    Create an API error for an unexpected error.

    :param reason: The reason for the unexpected error.
    :type reason: str

    :return: An instance of APIError representing the unexpected error.
    :rtype: APIError
    """
    return APIError("Unexpected Error", "005", as_status(500), field=reason)


def default_error(
    message: str,
    key: str = "000",
    status: HTTPStatus = as_status(400),
    field: Optional[str] = None,
):
    """
    Returns an APIError object with the specified message, key, status code, and optional field.

    :param message: The error message.
    :param key: The error key.
    :param status: The HTTP status code for the error.
    :param field: An optional field that caused the error.
    :return: An APIError object with the specified parameters.
    """
    return APIError(message=message, key=key, status=status, field=field)


class APIErrorResponse(Model):
    """
    Represents the response of an error in the api.
    """

    message: str = Field(
        ...,
        description="The error message returned by the api",
    )
    key: str = Field(
        ...,
        description="A unique key identifying the specific error returned by the api",
    )
    status: HTTPStatus = Field(
        ...,
        description="The HTTP status code associated with the error returned by the api",
    )
    path: str = Field(
        ...,
        description="The path of the api endpoint that triggered the error",
    )
    field: Optional[str] = Field(
        None,
        description="The specific field of the request that triggered the error, if applicable",
    )

    @validator("message")
    def validate_message(cls, value: str):
        """
        Applies the 'to_title_case' function to the 'message' field to capitalize the
        first letter of the error message, but only set title case to words with
        more than 3 letters or the first word.
        """
        return to_title_case(value)


error_responses = {item: {"model": APIErrorResponse} for item in error_response_status}


def to_title_case(
    string: str,
):  # sourcery skip: instance-method-first-arg-name
    """
    Convert a string to title case, but only set title case to words with
    more than 3 letters or the first word.
    """
    # Split the string into words.
    words = string.split()

    # Process the first word.
    if words:
        words[0] = words[0].capitalize()

    # Process the remaining words.
    for i, word in enumerate(words[1:]):
        if len(word) > 3:
            words[i + 1] = word.capitalize()

    # Join the words back into a string and return.
    return " ".join(words)


async def exception_handler(request: Request, exc: APIError):
    return ORJSONResponse(
        APIErrorResponse(**asdict(exc), path=request.url.path).dict(by_alias=True),
        status_code=exc.status,
        headers={"X-WWW-Error-Field": exc.field or ""},
    )


P = ParamSpec("P")
T = TypeVar("T")
Decorator = Callable[P, Coroutine[Any, Any, T]]


def not_found_if_none(target: str, field: str):
    def decorator(func: Decorator[P, T | None]) -> Decorator[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = await func(*args, **kwargs)
            if result is None:
                raise not_found_error(target, field)
            return result

        return wrapper

    return decorator

'''

DUNDER_EXC = """from .handlers import set_api_error_handler
from .exceptions import (
    APIError,
    not_found_error,
    already_exists_error,
    forbidden_error,
    not_authenticated,
    invalid_or_expired_token,
    field_error,
    unexpected_error,
    default_error,
    not_found_if_none,
)

__all__ = [
    "set_api_error_handler",
    "APIError",
    "not_found_error",
    "already_exists_error",
    "forbidden_error",
    "not_authenticated",
    "invalid_or_expired_token",
    "field_error",
    "unexpected_error",
    "default_error",
    "not_found_if_none",
]

"""

MAIN_FILE = Template(
    """from fastapi import FastAPI
{% if db %}    
from gyver.database import DatabaseAdapter
{% endif %}
from {{project_folder}} import routes
from {{project_folder}}.{{core_folder}} import settings
from {{project_folder}}.{{exceptions_folder}} import set_api_error_handler

def create_startup_handler(app: FastAPI):
    def _startup():
        {% if db %}app.state.database_provider = DatabaseAdapter(settings.db_config_factory())
        {% else %}# add handlers to be executed on initialization
        pass
        {% endif %}


    return _startup



def get_application(prefix: str = ""):
    app = FastAPI(
        title="{{project_as_title}}",
        openapi_url=f"{prefix}/openapi.json",
        docs_url=f"{prefix}/docs",
        redoc_url=f"{prefix}/redoc",
    )
    app.include_router(routes.router, prefix=prefix)

    app.add_event_handler("startup", create_startup_handler(app))
    set_api_error_handler(app)

    return app


app = get_application()


if __name__ = "__main__":
    import uvicorn

    uvicorn.run("{{project_folder}}.main:app", reload=True)

"""
)


DOCKERFILE = Template(
    """FROM python:{{pyver}}-slim as dependencies

# Installing default dependencies
RUN python -m pip install -Uq pip poetry

WORKDIR /var/www/web

# Copying project metadata
COPY pyproject.toml poetry.lock ./

# Setting up poetry
RUN poetry config virtualenvs.in-project true

# Installing project dependencies
RUN poetry install --only main

FROM python:{{pyver}}-slim

WORKDIR /var/www/web

#Setup Virtualenv
ENV VIRTUAL_ENV=/var/www/web/.venv
COPY --from=dependencies $VIRTUAL_ENV  $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copying source files
COPY . .

# Run migrations and execute app
ENTRYPOINT alembic upgrade head && \
    gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker -e CONFIG_ENV=prd --bind 0.0.0.0:8000 --log-level=info {{project_folder}}.{{main_api_file}}:app

# Expose app port
EXPOSE 8000

"""
)


COVERAGE_RC = Template(
    """# .coveragerc to control coverage.py
[run]
source = {{project_folder}}
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

"""
)


ALEMBIC_README = "Generic single-database configuration."

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

ALEMBIC_ENV = Template(
    '''# type: ignore
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from gyver.database import make_uri, default_metadata
from gyver.utils import FinderBuilder
from {{project_folder}}.{{core_folder}}.settings import db_config_factory

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
uri = make_uri(db_config_factory(), sync=True)
FinderBuilder().from_path(Path(__file__).parent.parent / {{project_folder}}).find()
target_metadata = default_metadata

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

    context.configure(
        url=uri,
        target_metadata=target_metadata,
        literal_binds=True,
        {% raw %}
        dialect_opts={{"paramstyle": "named"}},
        {% endraw %}
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    cfg = config.get_section(config.config_ini_section)
    cfg["sqlalchemy.url"] = uri
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
)

ALEMBIC_INI = Template(
    """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = ./{{alembic_folder}}

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
)

DOTENV_TEMPLATE = Template(
    """DB_NAME={{db.name}}
DB_USER={{db.user}}
DB_PASSWORD={{db.password}}
DB_HOST={{db.host}}
"""
)

POSTGRES_DOTENV = Template(
    """POSTGRES_USER={{db.user}}
POSTGRES_PASSWORD={{db.password}}
POSTGRES_DB={{db.name}}
"""
)
MYSQL_COMPAT_DOTENV = Template(
    """{{db_varname}}_USER={{db.user}}
{{db_varname}}_PASSWORD={{db.password}}
{{db_varname}}_ROOT_PASSWORD={{db.password}}
{{db_varname}}_DATABASE={{db.name}}
"""
)

MAKEFILE_TEMPLATE = Template(
    lead_spaces_as_tabs(
        """.PHONY: format run-dev test lint setup-localdb teardown-localdb

RUN := poetry run

format:
    @echo "Running black"
    @${RUN} black {{project_folder}} tests

    @echo "Running isort"
    @${RUN} isort {{project_folder}} tests

    @echo "Running autoflake"
    @${RUN} autoflake --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --expand-star-imports -ir {{project_folder}} tests

run-dev:
    @CONFIG_ENV=local ${RUN} uvicorn --host 127.0.0.1 --port 8000 {{project_folder}}.{{main_file}}:app --reload

run-as-prd:
    @gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker -e CONFIG_ENV=prd --bind 0.0.0.0:8000 --log-level=info {{project_folder}}.{{main_file}}:app

test:
    @CONFIG_ENV=local ${RUN} pytest tests
{% if db %}
{% if not_sqlite %}
setup-localdb:
    @{{docker_exec}} run --env-file .env-localdb -p {{db.port}}:{{db.dialect.default_port}} -d --name {{db.name}} docker.io/{{dialect_name}}

teardown-localdb:
    @{{docker_exec}} stop {{db.name}}
    @{{docker_exec}} rm -f {{db.name}}

{% endif %}
{% endif %}
"""
    )
)


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
