from enum import Enum
from functools import partial
from logging import Logger
from os import getenv
from typing import Callable, Optional, TypeVar, Union, overload

from stories.exc import EnvironmentNotSet


class Env(str, Enum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


T = TypeVar("T")


class Environment:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.__logger = logger

    @property
    def logger(self):
        return self.__logger

    def set_logger(self, logger: Logger):
        self.__logger = logger

    @staticmethod
    def default_parser(val: str) -> str:
        return val

    def _get(
        self,
        cond: bool,
        key: str,
        *,
        dev: str,
        parser: Optional[Callable[[str], T]] = None,
        fallback: Callable,
    ) -> T:
        val = getenv(key)
        if not val and cond:
            fallback()
        return (parser or self.default_parser)(val or dev)  # type: ignore

    def required(
        self,
        cond: bool,
        key: str,
        *,
        dev: str,
        parser: Optional[Callable[[str], T]] = None,
    ) -> T:
        def fallback():
            raise EnvironmentNotSet(key)

        return self._get(cond, key, dev=dev, parser=parser, fallback=fallback)

    def get(
        self, key: str, *, dev: str, parser: Optional[Callable[[str], T]] = None
    ) -> T:
        def fallback():
            if self.logger is not None:
                self.logger.warning(f"The key {key} is not set.")

        return self._get(
            True,
            key,
            dev=dev,
            parser=parser,
            fallback=fallback,
        )

    def required_if(self, cond: bool):
        def _required(
            key: str,
            *,
            dev: str,
            parser: Optional[Callable[[str], T]] = None,
        ) -> T:
            return self.required(cond, key, dev=dev, parser=parser)

        return _required

