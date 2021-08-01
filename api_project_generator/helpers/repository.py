from api_project_generator.helpers import request


class PypiRepository:
    def __init__(self) -> None:
        self._uri_template = "https://pypi.org/pypi/{package}/json"
    
    def get_package_info(self, package:str):
        return request.get(self._uri_template.format(package=package))

pypi_repository = PypiRepository()