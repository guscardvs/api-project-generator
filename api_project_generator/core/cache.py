import contextlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import sqlalchemy as sa
from appdirs import user_cache_dir
from gyver.attrs import define
from gyver.context import atomic
from gyver.database import (
    DatabaseAdapter,
    DatabaseConfig,
    Driver,
    SaContext,
    default_metadata,
    make_table,
)
from gyver.utils import lazyfield, timezone

DEFAULT_TTL = timedelta(hours=5)


@define
class Cache:
    _cache_dir: Optional[str] = None
    database_config: Optional[DatabaseConfig] = None

    def __post_init__(self):
        self.initialize()

    @lazyfield
    def cache_dir(self):
        cache_dir = self._cache_dir
        if cache_dir is None or not Path(cache_dir).exists():
            cache_dir = user_cache_dir("api-project-generator")
        os.makedirs(cache_dir, exist_ok=True)
        return Path(cache_dir)

    @lazyfield
    def context(self) -> SaContext:
        config = self.database_config or DatabaseConfig(
            Driver.SQLITE, f'/{(self.cache_dir / "cache.db").as_posix()}'
        )
        adapter = DatabaseAdapter(config)
        with adapter.engine.connect():
            pass
        return adapter.context()

    @lazyfield
    def table(self):
        if (table := default_metadata.tables.get("cache")) is not None:
            return table
        return make_table(
            "cache",
            sa.Column("key", sa.Text, primary_key=True),
            sa.Column("content", sa.Text),
            sa.Column("expiration", sa.DateTime),
        )

    def initialize(self):
        with self.context as conn:
            self.table.create(conn, checkfirst=True)
            with atomic(self.context) as conn:
                conn.execute(
                    self.table.delete().where(self.table.c.expiration < timezone.now())
                )

    def get(self, key: str):
        with self.context as conn:
            result = conn.execute(
                self.table.select().where(
                    self.table.c.key == key,
                    self.table.c.expiration >= timezone.now(),
                )
            )
            if val := result.mappings().first():
                return val["content"]
            raise CacheMiss(key)

    def set(self, key: str, content: str, ttl: Optional[datetime] = None) -> None:
        with atomic(self.context) as conn:
            conn.execute(self.table.delete().where(self.table.c.key == key))
            conn.execute(
                self.table.insert().values(
                    key=key,
                    content=content,
                    expiration=ttl or (timezone.now() + DEFAULT_TTL),
                )
            )

    def set_file(self, filename: str, content: bytes):
        file_path = self.cache_dir / filename
        with open(file_path, "wb") as file:
            file.write(content)

    def get_file(self, filename: str):
        file_path = self.cache_dir / filename
        try:
            with open(file_path, "rb") as file:
                return file.read()
        except FileNotFoundError as err:
            raise CacheMiss from err

    def delete(self, key: str) -> None:
        with atomic(self.context) as conn:
            conn.execute(self.table.delete().where(self.table.c.key == key))

    def delete_file(self, filename: str) -> None:
        file_path = self.cache_dir / filename
        with contextlib.suppress(FileNotFoundError):
            os.remove(file_path)

    def cleankeys(self, keys: List[str]) -> None:
        with atomic(self.context) as conn:
            conn.execute(self.table.delete().where(self.table.c.key.in_(keys)))

    def cleanfiles(self, filenames: List[str]) -> None:
        for filename in filenames:
            file_path = self.cache_dir / filename
            with contextlib.suppress(FileNotFoundError):
                os.remove(file_path)

    def destroy(self) -> None:
        self.cleankeys(self.get_all_keys())
        self.cleanfiles(self.get_all_files())

    def get_all_keys(self) -> List[str]:
        with self.context as conn:
            result = conn.execute(self.table.select())
            return [row["key"] for row in result.mappings()]

    def get_all_files(self) -> List[str]:
        files = []
        for file_name in os.listdir(self.cache_dir):
            file_path = self.cache_dir / file_name
            if file_path.is_file():
                files.append(file_name)
        return files


class CacheMiss(Exception):
    pass
