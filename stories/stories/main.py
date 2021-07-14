from sys import prefix

from fastapi import FastAPI

from stories import api
from stories.providers import DatabaseProvider, HttpProvider
from stories.exc import set_api_error_handler

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
        title="Adapty Event Listener",
        openapi_url=f"{prefix}/openapi.json",
        docs_url=f"{prefix}/docs",
        redoc_url=f"{prefix}/redoc",
    )
    _app.include_router(api.router, prefix=f"{prefix or '/'}")

    _app.add_event_handler("startup", create_startup_handler(_app))
    _app.add_event_handler("shutdown", create_shutdown_handler(_app))
    set_api_error_handler(_app)

    return _app


app = get_application()


def main():
    import uvicorn

    uvicorn.run("adapty_listener.main:app", reload=True)

