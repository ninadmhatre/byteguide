"""
Contains the data types used by the server.
"""
import enum
import json
import typing as t
from pathlib import Path

from loguru import logger as log


class Status(enum.Enum):
    """
    Represents a status.
    """
    OK = "OK"
    ERROR = "ERROR"
    NOT_FOUND = "NOT_FOUND"
    NOT_REGISTERED = "NOT_REGISTERED"
    NOT_A_VALID_ZIP_FILE = "NOT_A_VALID_ZIP_FILE"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    INVALID_NAME = "INVALID_NAME"
    INVALID_VERSION = "INVALID_VERSION"
    INVALID_UNIQUE_KEY = "INVALID_UNIQUE_KEY"


class ProjectEntry: # pylint: disable=too-few-public-methods
    """
    Represents a project entry.
    """

    def __init__(self, path: Path):
        self.path = path
        self.metadata = self._load_metadata()
        self.versions = self.metadata.get("versions", [])
        self.has_changelog = self.path.joinpath("changelog.html").is_file()

    def _load_metadata(self) -> t.Dict:
        """
        Load the project metadata.

        Returns:
            The project metadata.
        """
        metadata_path = self.path.joinpath("metadata.json")

        if not metadata_path.exists():
            log.warning(f"Project {self.path} does not contain metadata.json")
            return {}

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("versions"):
            log.warning(f"Project {self.path} metadata does not contain any versions")
            return data

        versions = []

        for ver, ver_meta in data["versions"].items():
            upload_date = ver_meta["upload-date"].split(" ")[0]
            versions.append((ver, upload_date))

        data["versions"] = versions

        return data

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{self.path=}, {self.has_changelog=}, {self.metadata=}, {self.versions=})"
        ).replace("self.", "")
