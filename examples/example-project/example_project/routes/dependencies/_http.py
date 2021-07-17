from fastapi import Request
from example_project.providers import HttpProvider

def get_http_provider(request: Request) -> HttpProvider:
    return request.app.state.http_provider

