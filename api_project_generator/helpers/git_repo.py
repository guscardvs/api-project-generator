from pathlib import Path

from git import Repo


def init_repository(path: Path) -> Repo:
    return Repo.init(path)

