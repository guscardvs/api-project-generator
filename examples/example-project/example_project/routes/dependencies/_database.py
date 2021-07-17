from fastapi import Request
from example_project.providers import DatabaseProvider

def get_database_provider(request: Request) -> DatabaseProvider:
    return request.app.state.database_provider

