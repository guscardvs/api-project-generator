from fastapi import Request
from stories.providers import DatabaseProvider

def get_database_provider(request: Request) -> DatabaseProvider:
    return request.app.state.database_provider

