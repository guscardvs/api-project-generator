from example_project.providers import DatabaseProvider
from fastapi import Request


def get_database_provider(request: Request) -> DatabaseProvider:
    return request.app.state.database_provider

