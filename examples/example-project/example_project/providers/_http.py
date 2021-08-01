import asyncio
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Callable, Optional, TypeVar
from urllib.parse import urlparse

from aiohttp import ClientSession, ContentTypeError
from example_project.core.settings import logger
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
        self.clients: dict[str, ClientSession] = {}
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
        return self.request("GET", url, params=params or {}, **kwargs)

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] = None,
        data: dict[str, Any] = None,
        **kwargs,
    ):
        if json:
            return self.request("POST", url, json=json or {}, **kwargs)
        return self.request("POST", url, data=data or {}, **kwargs)

