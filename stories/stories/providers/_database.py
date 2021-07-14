from contextlib import asynccontextmanager
from typing import Literal, Optional

from stories.core import settings
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class DatabaseProvider:
    def __init__(self, conn_uri: Optional[str] = None) -> None:
        self.engine = self._create_engine(conn_uri)
        self.sessionmaker = self._create_sessionmaker()

    @staticmethod
    def get_connection_uri():
        return "mysql://{user}:{passwd}@{host}:3306/{name}".format(
            user=settings.DB_USER,
            passwd=settings.DB_PASSWD,
            host=settings.DB_HOST,
            name=settings.DB_NAME,
        )

    @classmethod
    def get_driver_conn_uri(cls, driver: Literal["aiomysql", "pymysql"]):
        return cls.get_connection_uri().replace("mysql", f"mysql+{driver}")

    def _create_engine(self, conn_uri: Optional[str]):
        if conn_uri:
            return create_async_engine(conn_uri)
        return create_async_engine(
            self.get_driver_conn_uri("aiomysql"), pool_size=20, max_overflow=0
        )

    def _create_sessionmaker(self):
        return sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def get_session(self):
        async with self.sessionmaker() as session:
            yield session

    @asynccontextmanager
    async def begin(self):
        async with self.sessionmaker() as session:
            async with session.begin():
                yield session

