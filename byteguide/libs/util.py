"""
Provides utility methods.
"""
import json
import re
import typing as t
from pathlib import Path

from loguru import logger as log

from byteguide.libs.dtypes import ProjectEntry


def project_sort_key(project: ProjectEntry) -> str:
    """
    Get the sort key for a project.

    Args:
        project: The project.

    Returns:
        The sort key.
    """
    return project.metadata["name"].lower()


def file_from_request(request) -> str:
    """
    Get the uploaded file from a POST request, which should contain exactly one file.

    Args:
        request: The POST request.

    Returns:
        The uploaded file.
    """
    uploaded_files = list(request.files.values())

    if len(uploaded_files) > 1:
        log.warning("Only one file can be uploaded for each request. " "Only the first file will be used.")
    elif len(uploaded_files) == 0:
        raise ValueError("Request does not contain uploaded file")

    return uploaded_files[0]


class Validators:
    @staticmethod
    def is_valid_version(version: str) -> bool:
        return Validators.is_alphanumeric(version, [".", "-"])

    @staticmethod
    def is_valid_name(name: str) -> bool:
        return Validators.is_alphanumeric(name, ["-", "_"])

    @staticmethod
    def is_alphanumeric(val: str, additional: t.List[str]) -> bool:
        regex = re.compile(r"^[a-zA-Z0-9{}]+$".format("".join(additional)))
        return regex.match(val) is not None


def get_directory_listing(path: str | Path) -> t.List[ProjectEntry]:
    result = []

    if isinstance(path, str):
        path = Path(path)

    for entry in path.iterdir():
        if entry.is_dir():
            result.append(ProjectEntry(entry))

    return result


def validate_register_project(data: t.Dict) -> t.List[str]:
    """
    Validate the project metadata.

    Args:
        data: The project metadata.

    Returns:
        A tuple of (valid, errors).
    """
    errors = []

    if not data.get("name"):
        errors.append("Project 'name' is required!")

    if not data.get("description"):
        errors.append("Project 'description' is required!")

    if not data.get("owner"):
        errors.append("Project 'owner' is required!")

    if not data.get("owner-email"):
        errors.append("Project owner email is required!")

    if not data.get("programming-lang"):
        errors.append("Project programming language is required!")

    if "tags" in data and not isinstance(data["tags"], list):  # optional
        errors.append("Project 'tags' must be a list!")

    return errors
