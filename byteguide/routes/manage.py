""" Manage routes for the byteguide. """

from flask import Blueprint, jsonify, request
from loguru import logger as log

from byteguide.config import config
from byteguide.libs import util
from byteguide.libs.fs import DocsDirScanner, MetaDataHandler, Uploader

manage_routes = Blueprint("manage", __name__, template_folder="templates", url_prefix="/manage")

uploader = Uploader()


@manage_routes.route("/register", methods=["POST"])
def register():
    """
    Register a project passed in a JSON doc. JSON doc must include a project name, description, and version.
    owner of the project, owner email address, project lang and optional project tags.

    Example:
    ```bash
    $ cat register.json
    {
        "name": "Sample-Proj",
        "description": "This is a sample project",
        "owner": "Ninad Mhatre",
        "owner-email": "ninad.mhatre@gmail.com",
        "programming-lang": "Python",
        "tags": ["python", "sample", "project"]
    }

    $ curl -X POST -d @register.json -H 'Content-Type: application/json' http://127.0.0.1:29000/manage/register
    ```

    Returns:
        A JSON doc with the following keys:
        - `message`: message indicating success or failure of the registration
        - `project`: name of the project
        - `unique-key`: unique key for the project
    """

    register_project = request.get_json()

    errors = util.validate_register_project(register_project)

    if errors:
        return jsonify({"message": "failed to register project", "errors": errors}), 400

    proj_name = register_project["name"]
    proj_path = config.docfiles_dir.joinpath(proj_name)

    result = {"message": "", "project": register_project["name"], "unique-key": ""}

    metadata_handler = MetaDataHandler(proj_name)
    dir_scan = DocsDirScanner()

    all_projects = dir_scan.get_all_projects()
    existing_projs = [proj.lower() for proj in all_projects]

    if proj_path.exists() or proj_name.lower() in existing_projs:
        proj_json = metadata_handler.read_metadata()
        result["message"] = f"project ['{proj_name.lower()}'] already registered!"
        result["unique-key"] = proj_json["unique-key"]
    else:
        proj_path.mkdir()
        unique_id = metadata_handler.init_metadata(register_project)
        result["message"] = "project registered successfully!"
        result["unique-key"] = unique_id

    return jsonify(result)


@manage_routes.route("/upload", methods=["POST"])
def upload():
    """
    Upload a zip file containing the project `version` documentation.

    Note:
    1. The zip file must contain an `index.html` file at the root.
    2. 'Project' must be registered first!

    Example:
    ```bash
    $ curl -X POST -d @file.zip \
        -F unique-key=unique-key \
        -F reupload=true \
        http://127.0.0.1:5000/manage/upload
    ```

    Returns:
        A JSON doc with the following keys:
        - `status`: status of the upload
        - `message`: message indicating success or failure of the upload
    """
    if config.readonly:
        return jsonify({"status": "failed", "message": "Readonly mode is enabled."}), 403

    if not request.files:
        return jsonify({"status": "failed", "message": "Request is missing a zip file."}), 400

    unique_key = request.form.get("unique-key", None)
    reupload = request.form.get("reupload", "false")

    reupload = reupload.lower() == "true"

    # zip file name should be "proj_name-version.zip"
    try:
        uploaded_file = util.file_from_request(request)
        status = uploader.upload(uploaded_file, uniq_key=unique_key, reupload=reupload)
    except Exception as e:  # pylint: disable=broad-except
        log.error(e)
        response = {"status": "failed", "message": str(e)}
    else:
        response = {"status": status.value, "message": ""}

    return jsonify(response)


@manage_routes.route("/delete", methods=["POST"])
def delete():
    """
    Delete a specific version of a package. Deletion details are sent as a JSON doc.
    Admin will be notified on version deletion.
    """
