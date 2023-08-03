import sys
from typing import Optional

from gyver.attrs import define
from gyver.database import Driver
from gyver.database.drivers.utils import resolve_driver
from gyver.utils import lazyfield

from api_project_generator.core.config import Config
from api_project_generator.models.version import VersionType

from .project_organization import ProjectOrganization


@define
class ProjectInfo:
    config: Config
    name: str
    version: str
    version_type: VersionType
    description: str
    fullname: str
    email: str
    driver: Optional[Driver]
    organization: ProjectOrganization
    pyver: Optional[str] = None

    @lazyfield
    def dialect(self):
        return self.driver and resolve_driver(self.driver)

    @lazyfield
    def effective_pyver(self):
        return self.pyver or f"{sys.version_info.major}.{sys.version_info.minor}"
