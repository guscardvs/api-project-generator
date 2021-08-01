from example_project.providers import HttpProvider
from fastapi import Request


def get_http_provider(request: Request) -> HttpProvider:
    return request.app.state.http_provider

