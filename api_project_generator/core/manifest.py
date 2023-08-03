from typing import Any

from api_project_generator.models.project_info import ProjectInfo


def append_manifest(mapping: dict[str, Any], project_info: ProjectInfo) -> None:
    """
    Appends fields from the given `ProjectInfo` object to the TOML mapping.

    :param mapping: The TOML mapping to append the fields to.
    :param project_info: The `ProjectInfo` object containing the fields to append.
    :return: None
    """
    # Ensure the necessary nested mappings exist
    if "tool" not in mapping:
        mapping["tool"] = {}

    # Append fields from ProjectInfo
    mapping["tool"]["api_project"] = {
        "name": project_info.name,
        "version": project_info.version,
        "version_type": project_info.version_type.value,
        "description": project_info.description,
        "fullname": project_info.fullname,
        "email": project_info.email,
        "driver": project_info.driver,
        "organization": project_info.organization.value,
        "pyver": project_info.effective_pyver,
        "modules": [],
    }
