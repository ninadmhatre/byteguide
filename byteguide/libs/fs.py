from collections import OrderedDict
import os
import shutil
from typing import Any
import zipfile
from pathlib import Path
import typing as t
import re
import tempfile
import json
import uuid
import datetime as dt

import natsort
from loguru import logger as log
from werkzeug.datastructures.file_storage import FileStorage

from byteguide.libs.util import ProjectEntry, Validators, get_directory_listing, project_sort_key
from byteguide.libs.dtypes import Status
from byteguide.config import config


class Uploader:
    @staticmethod
    def is_valid_zip_file(filename: t.Any) -> bool:
        if isinstance(filename, zipfile.ZipFile):
            if "index.html" not in filename.namelist():
                log.error("Failed to find root index file!")
                return False
        else:
            log.error(f"Invalid archive file type: {type(filename)}")
            return False

        return True

    def _retrieve_name_and_version_from_zip(self, filename: FileStorage) -> t.Tuple[str, str]:
        """
        Retrieve project name and version from the zip file name.

        Args:
            filename (Path): zip file name.

        Returns:
            Tuple[str, str]: project name and version.
        """
        name = filename.filename

        assert name.endswith(".zip"), "File must be a .zip file! (e.g. proj_name-version.zip)"

        name = name[:-4]
        name, version = name.rsplit("-", maxsplit=1)
        return name, version

    def upload(self, filename: FileStorage, uniq_key: str, reupload: bool = False) -> Status:
        """
        upload a version zip file to byteguide.

        Args:
            filename (Path): uploaded file to be decomressed and stored.
            uniq_key (str): unique key for the project.
            reupload (bool, optional): reupload version. Defaults to False.

        Returns:
            Status: One of the Status enum values.
        """

        name, version = self._retrieve_name_and_version_from_zip(filename)

        projdir = config.docfiles_dir.joinpath(name)
        verdir = projdir.joinpath(version)

        if not projdir.exists():
            return Status.NOT_REGISTERED

        if not Validators.is_valid_name(name):
            return Status.INVALID_NAME

        if not Validators.is_valid_version(version):
            return Status.INVALID_VERSION

        existing_metadata = MetaDataHandler(project=name).metadata
        if existing_metadata["unique-key"] != uniq_key:
            return Status.INVALID_UNIQUE_KEY

        if verdir.exists() and not reupload:
            return Status.ALREADY_EXISTS

        if not verdir.exists():
            verdir.mkdir()

        # This is insecure, we are only accepting things from trusted sources.
        with zipfile.ZipFile(filename) as compressed_file:
            if self.is_valid_zip_file(compressed_file):
                try:
                    # Extract full archive to temporary directory
                    temp_dir = tempfile.mkdtemp()
                    compressed_file.extractall(temp_dir)

                    shutil.rmtree(verdir)  # clear possibly existing target dir
                    shutil.move(temp_dir, verdir)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    log.error(e)
                    return Status.ERROR
                else:
                    self.update_version_metadata(name, version)
                    self.create_latest_symlink(name)
                    return Status.OK
            else:
                return Status.NOT_A_VALID_ZIP_FILE

    def delete(self, project: str, version: str) -> t.Tuple[bool, str]:
        version_dir = config.docfiles_dir.joinpath(project, version)

        if not version_dir.exists():
            return False, "Version not found!"

        try:
            shutil.rmtree(version_dir)
        except Exception as e:
            log.error(e)
            return False, str(e)
        else:
            MetaDataHandler(project).delete_version(version)
            return True, "Version deleted successfully!"

    @staticmethod
    def create_latest_symlink(name: str):
        latest_ver = MetaDataHandler(name).get_latest_version()
        proj_dir = config.docfiles_dir.joinpath(name)
        latest_link = proj_dir.joinpath("latest")

        if latest_link.exists():
            latest_link.unlink()

        latest_link.symlink_to(latest_ver)

    @staticmethod
    def update_version_metadata(project: str, version: str) -> str:
        log.info(f"Updating metadata for project {project} version {version}")

        proj_metadata = MetaDataHandler(project)
        proj_metadata.read_metadata()

        log.info(f"Current metadata: {proj_metadata.metadata}")

        proj_metadata.add_version(version)

        return proj_metadata.get_latest_version()


class MetaDataHandler:
    def __init__(self, project: str):
        """
        Handles metadata for projects. Metadata is stored in a JSON file named `metadata.json` in the project directory.

        Metadata is a JSON object with the following keys:

        - `name`: name of the project
        - `description`: description of the project
        - `owner`: name of the project owner
        - `owner-email`: email address of the project owner
        - `programming-lang`: programming language used in the project
        - `tags`: list of tags for the project
        - `unique-key`: unique key for the project
        - `versions`: list of versions of the project
        - `keep-latest-n`: latest N versions of the project [optional] [not implemented yet]
        - `notify-owner-on-update`: notify project owner when a new version is uploaded [optional] [not implemented yet]

        Args:
            project (str): name of the project.
        """
        self.project = project
        self.docs_dir = config.docfiles_dir
        self.project_dir = self.docs_dir.joinpath(project)
        self.meta_file_name = "metadata.json"
        self.metadata = self.read_metadata()

    def _get_metadata_file(self) -> Path:
        return self.project_dir.joinpath(self.meta_file_name)

    def read_metadata(self) -> t.Dict:
        metadata_file = self._get_metadata_file()

        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            return metadata
        return {}

    def init_metadata(self, metadata: t.Dict) -> str:
        metadata_file = self._get_metadata_file()

        if metadata_file.exists():
            raise FileExistsError(f"Metadata file for project {metadata_file} already exists.")

        unique_key = str(uuid.uuid4())

        metadata["unique-key"] = unique_key

        # conert tags, if any, to lowercase and remove duplicates
        if "tags" in metadata:
            metadata["tags"] = list(set([tag.lower() for tag in metadata["tags"]]))

        # convert programming language to lowercase
        if "programming-lang" in metadata:
            metadata["programming-lang"] = metadata["programming-lang"].lower()

        self.save(metadata)

        return unique_key

    def add_version(self, version: str) -> bool:
        if "versions" not in self.metadata:
            self.metadata["versions"] = {}

        _upload_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.metadata["versions"][version] = {"upload-date": _upload_time}
        self.sort_versions()
        self.save()

    def delete_version(self, version: str) -> bool:
        if version in self.metadata["versions"]:
            del self.metadata["versions"][version]
            self.sort_versions()
            self.save()

    def sort_versions(self) -> bool:
        sorted = OrderedDict()

        for version in natsort.natsorted(self.metadata["versions"], reverse=True):
            sorted[version] = self.metadata["versions"][version]

        self.metadata["versions"] = sorted

    def get_latest_version(self, n: int = 1) -> str:
        if "versions" not in self.metadata:
            return ""

        return list(self.metadata["versions"])[0]

    def save(self, metadata: t.Optional[t.Dict] = None):
        metadata = metadata or self.metadata
        metadata_file = self._get_metadata_file()

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)


class DocsDirScanner:
    def __init__(self) -> None:
        self.docs_dir = config.docfiles_dir

    def projects_as_template_data(self, all_projects: t.List[ProjectEntry]) -> t.List[t.Dict[str, t.Any]]:
        projects = OrderedDict()

        for project in natsort.natsorted(all_projects, key=project_sort_key):
            project_metadata = project.metadata

            if "versions" in project_metadata:
                versions = natsort.natsorted(project_metadata["versions"], key=lambda x: x[0])
            else:
                versions = []

            project_metadata["versions"] = versions

            projects[project_metadata["name"]] = project_metadata

        return projects

    def get_proj_metadata(self, project: str) -> t.Optional[t.Dict[str, t.Any] | None]:
        proj_dir = self.docs_dir.joinpath(project)

        if not proj_dir.is_dir():
            return None

        return MetaDataHandler(project).metadata

    def get_proj_versions(self, project: str, skip_latest: bool = False) -> t.Dict[str, t.Any]:
        docfiles_dir = config.docfiles_dir
        proj_dir = docfiles_dir.joinpath(project)

        if not docfiles_dir.is_dir():
            return {}

        project_metadata = self.get_proj_metadata(proj_dir)

        if "versions" in project_metadata:
            versions = natsort.natsorted(project_metadata["versions"], key=lambda x: x[0])
        else:
            versions = []

        if skip_latest:
            project_metadata["versions"] = ["latest", *versions]
        else:
            project_metadata["versions"] = versions

        return project_metadata

    def get_all_projects(self, docfiles_dir: t.Optional[Path] = None) -> t.Dict[str, t.List[str]]:
        """
        Create the list of the projects.

        The list of projects is computed by walking the `docfiles_dir` and
        searching for project paths (<project-name>/<version>/index.html)
        """
        docfiles_dir = docfiles_dir or config.docfiles_dir

        if not docfiles_dir.is_dir():
            return []

        all_projects: t.List[ProjectEntry] = get_directory_listing(path=docfiles_dir)

        return self.projects_as_template_data(all_projects)

    def search_by_filter(
        self,
        lang: t.Optional[str] = None,
        pattern: t.Optional[str] = None,
        tag: t.Optional[str] = None,
        docfiles_dir: t.Optional[Path] = None,
    ) -> t.Dict[str, t.List[str]]:
        docfiles_dir = docfiles_dir or config.docfiles_dir

        if not docfiles_dir.is_dir():
            return []

        all_proj_dirs = get_directory_listing(path=docfiles_dir)

        filtered_result = self.apply_filter(all_proj_dirs, lang, pattern, tag)

        if filtered_result:
            return self.projects_as_template_data(filtered_result)
        return {}

    def apply_filter(
        self,
        all_projects: t.OrderedDict[str, t.Dict[str, t.Any]],
        lang: t.Optional[str],
        pattern: t.Optional[str],
        tag: t.Optional[str],
    ) -> t.Dict[str, t.List[str]]:
        final_projects = all_projects

        if pattern:
            try:
                pattern = re.compile(pattern)
                final_projects = [proj for proj in final_projects if pattern.match(proj.metadata["name"])]
            except Exception as e:
                log.exception(e)
                final_projects = []

        if lang:
            final_projects = [proj for proj in final_projects if proj.metadata["programming-lang"] == lang.lower()]

        if tag:
            final_projects = [proj for proj in final_projects if tag.lower() in proj.metadata["tags"]]

        return final_projects


docs_dir_scanner = DocsDirScanner()
