from fastapi import FastAPI

from example_project import routes
from example_project.providers import DatabaseProvider, HttpProvider
from example_project.exc import set_api_error_handler

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
        title="Example Project",
        openapi_url=f"{prefix}/openapi.json",
        docs_url=f"{prefix}/docs",
        redoc_url=f"{prefix}/redoc",
    )
    _app.include_router(routes.router, prefix=f"{prefix}")

    _app.add_event_handler("startup", create_startup_handler(_app))
    _app.add_event_handler("shutdown", create_shutdown_handler(_app))
    set_api_error_handler(_app)

    return _app


app = get_application()


def main():
    import uvicorn

    uvicorn.run("example_project.main:app", reload=True)

