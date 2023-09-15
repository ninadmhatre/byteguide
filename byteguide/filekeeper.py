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
from codecs import open
from loguru import logger as log

from byteguide.libs.util import Validators
from byteguide.config import config


def sort_by_version(x: t.Dict[str, str]):
    # See http://natsort.readthedocs.io/en/stable/examples.html
    return x["version"].replace(".", "~") + "z"


def _is_valid_doc_version(folder: str) -> bool:
    """
    Test if a version folder contains valid documentation.

    A vaersion folder contains documentation if:
    - is a directory
    - contains an `index.html` file
    """
    folder = Path(folder)

    if folder.is_dir() and folder.joinpath("index.html").exists():
        return True
    return False




# def find_root_dir(compressed_file, file_ext=".html"):
#     """
#     Determines the documentation root directory by searching the top-level index file.
#     """

#     if isinstance(compressed_file, zipfile.ZipFile):
#         index_files = [
#             member.filename
#             for member in compressed_file.infolist()
#             if not member.is_dir()
#             and os.path.basename(member.filename) == f"index{file_ext}"
#         ]
#     else:
#         raise TypeError(f"Invalid archive file type: {type(compressed_file)}")

#     if not index_files:
#         raise FileNotFoundError("Failed to find root index file!")

#     root_index_file = sorted(
#         index_files, key=lambda filename: len(filename.split(os.sep))
#     )[0]

#     return os.path.dirname(root_index_file)


# def unpack_project(uploaded_file, proj_metadata, docfiles_dir):
#     projdir = os.path.join(docfiles_dir, proj_metadata["name"])
#     verdir = os.path.join(projdir, proj_metadata["version"])

#     if not os.path.isdir(verdir):
#         os.makedirs(verdir)

#     # Overwrite project description only if a (non empty) new one has been
#     # provided
#     descr = proj_metadata.get("description", "")
#     if len(descr) > 0:
#         descrpath = os.path.join(projdir, "description.txt")
#         with open(descrpath, "w", encoding="utf-8") as f:
#             f.write(descr)

#     # This is insecure, we are only accepting things from trusted sources.
#     with util.FileExpander(uploaded_file) as compressed_file:
#         # Determine documentation root dir by finding top-level index file
#         root_dir = find_root_dir(compressed_file)

#         # Extract full archive to temporary directory
#         temp_dir = tempfile.mkdtemp()
#         compressed_file.extractall(temp_dir)

#         # Then, only move root directory to target dir
#         shutil.rmtree(verdir)  # clear possibly existing target dir
#         shutil.move(
#             os.path.join(temp_dir, root_dir), verdir
#         )  # only move documentation root dir

#         if os.path.isdir(temp_dir):  # cleanup temporary directory (if it still exists)
#             shutil.rmtree(temp_dir)


# def delete_files(name, version, docfiles_dir, entire_project=False):
#     remove = os.path.join(docfiles_dir, name)
#     if not entire_project:
#         remove = os.path.join(remove, version)
#     if os.path.exists(remove):
#         shutil.rmtree(remove)


def _has_latest(versions):
    return any(v["version"] == "latest" for v in versions)


def insert_link_to_latest(projects: t.List[t.Dict[str, t.Any]]):
    """For each project in ``projects``,
    will append a "latest" version that links to a certain location
    (should not be to static files).
    Will not add a "latest" version if it already exists.

    :param projects: Project dicts to mutate.
    :param template: String to turn into a link.
      Should have a ``%(project)s`` that will be replaced with the project name.
    """
    for p in projects:
        if _has_latest(p["versions"]):
            continue

        p["versions"].append({"version": "latest", "link": f"{p['name']}/latest"})


# class Uploader:
#     @staticmethod
#     def is_valid_zip_file(filename: t.Any) -> bool:
#         if isinstance(filename, zipfile.ZipFile):
#             if "index.html" not in filename.namelist():
#                 log.error("Failed to find root index file!")
#                 return False
#         else:
#             log.error(f"Invalid archive file type: {type(filename)}")
#             return False

#         return True

#     def upload(self, filename: Path, name: str, version: str, uniq_key: str, reupload: bool = False) -> Status:
#         """
#         upload a version zip file to byteguide.

#         Args:
#             filename (Path): uploaded file to be decomressed and stored.
#             name (str): project name.
#             version (str): project version.
#             uniq_key (str): unique key for the project.
#             reupload (bool, optional): reupload version. Defaults to False.

#         Returns:
#             Status: One of the Status enum values.
#         """
#         projdir = config.docfiles_dir.joinpath(name)
#         verdir = projdir.joinpath(version)

#         if not projdir.exists():
#             return Status.NOT_REGISTERED

#         if not Validators.is_valid_name(name):
#             return Status.INVALID_NAME

#         if not Validators.is_valid_version(version):
#             return Status.INVALID_VERSION

#         read_existing_metadata = MetaDataHandler().read_metadata(name)
#         if read_existing_metadata["unique-key"] != uniq_key:
#             return Status.INVALID_UNIQUE_KEY

#         if verdir.exists() and not reupload:
#             return Status.ALREADY_EXISTS

#         if not verdir.exists():
#             verdir.mkdir()

#         # This is insecure, we are only accepting things from trusted sources.
#         with zipfile.ZipFile(filename) as compressed_file:
#             if self.is_valid_zip_file(compressed_file):
#                 try:
#                     # Extract full archive to temporary directory
#                     temp_dir = tempfile.mkdtemp()
#                     compressed_file.extractall(temp_dir)

#                     shutil.rmtree(verdir)  # clear possibly existing target dir
#                     shutil.move(temp_dir, verdir)
#                     shutil.rmtree(temp_dir, ignore_errors=True)
#                 except Exception as e:
#                     log.error(e)
#                     return Status.ERROR
#                 else:
#                     return Status.OK
#             else:
#                 return Status.NOT_A_VALID_ZIP_FILE

#     def delete(self, project: str, version: str) -> t.Tuple[bool, str]:
#         version_dir = config.docfiles_dir.joinpath(project, version)

#         if not version_dir.exists():
#             return False, "Version not found!"

#         try:
#             shutil.rmtree(version_dir)
#         except Exception as e:
#             log.error(e)
#             return False, str(e)
#         else:
#             return True, "Version deleted successfully!"

#     def update_version_metadata(project: str, version: str):
#         proj_metadata = MetaDataHandler(project)
#         proj_metadata.read_metadata()

#         if version not in proj_metadata.metadata["versions"]:
#             proj_metadata.add_version(version)