DEFAULT_API_DEPENDENCIES = {
    "fastapi",
    "pydantic[email]",
    "uvicorn",
    "aiohttp",
    "python-dotenv",
    "sqlalchemy",
    "aiomysql",
    "alembic",
    "asyncpg",
    "psycopg2"
}
DEFAULT_DEV_DEPENDENCIES = {
    "pytest",
    "pylint",
    "black",
    "pytest-cov",
    "pytest-asyncio",
    "sqlalchemy2-stubs",
    "faker",
}

DEFAULT_DEPLOY_DEPENDENCIES = {
    "httptools",
    "uvloop",
    "gunicorn",
    "circus",
}
