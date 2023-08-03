import sys
from pathlib import Path

import tomlkit
from appdirs import user_cache_dir
from gyver.attrs import asdict, define, fromdict
from gyver.utils import cache, lazyfield

from api_project_generator.models.project_organization import ProjectOrganization
from api_project_generator.models.version import VersionType


@define
class Config:
    pypi_url: str
    gitignore_url: str
    default_ide: str
    default_cache_dir: str
    default_docker_executable: str
    default_pyver: str
    default_organization: ProjectOrganization
    default_version_type: VersionType

    @lazyfield
    def cache_dir(self):
        return Path(self.default_cache_dir)


cache_dir = Path(user_cache_dir("api-project-generator"))
cache_dir.mkdir(exist_ok=True)
config_cache = cache_dir / "api-project.toml"


@cache
def get_config() -> Config:
    config_cache = cache_dir / "api-project.toml"
    if not config_cache.exists():
        config = Config(
            pypi_url="https://pypi.org/simple",
            gitignore_url="https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore",
            default_ide="",
            default_cache_dir=str(cache_dir),
            default_docker_executable="",
            default_pyver=f"{sys.version_info.major}.{sys.version_info.minor}",
            default_organization=ProjectOrganization.STRUCTURAL,
            default_version_type=VersionType.SEMVER,
        )
        set_config(config)
    else:
        with open(config_cache) as stream:
            config = fromdict(Config, tomlkit.load(stream))
    return config


def set_config(config: Config):
    with open(config_cache, "w") as stream:
        tomlkit.dump(asdict(config), stream)
