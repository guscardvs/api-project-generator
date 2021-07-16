from pathlib import Path

from git import Repo


def init_repository(path: Path) -> Repo:
    return Repo.init(path)


def create_base_branches(repo: Repo) -> None:
    repo.create_head("master")
    develop_head = repo.create_head("develop")
    repo.head.reference = develop_head
