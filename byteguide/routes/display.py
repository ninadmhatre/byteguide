from pathlib import Path

from flask import Blueprint, render_template, jsonify, redirect, request

from byteguide.libs.fs import docs_dir_scanner
from byteguide.config import config

display_routes = Blueprint("browse", __name__, template_folder="templates", url_prefix="/browse")


@display_routes.route("/", methods=["GET"])
def browse_all():
    """
    Browse all projects uploaded to byteguide.

    Example:
        GET /browse

    Returns:
        A list of projects, each with a list of versions.
    """
    projects = docs_dir_scanner.get_all_projects()
    return render_template("browse.html", projects=projects, config=config, show_search=True)


@display_routes.route("/<project>/<version>/")
def browse_proj_ver(project: str, version: str):
    """
    Fetch the specific version of the project.

    Args:
        project (str): name of the project whose latest version is to be fetched.
        version (str): version of the project to be fetched.

    Example:
        GET /browse/<project>/<version>

    Returns:
        Get the latest version of the project.
    """
    info = docs_dir_scanner.get_proj_versions(project)

    if version in info["versions"]:
        return redirect("/".join([config.docfiles_link_root, project, version, "index.html"]))

    return jsonify({"error": f"Project {project} not found"}), 404


@display_routes.route("/search", methods=["GET"])
def search():
    """
    search for a project matching specific search criteria.

    Args:
        pattern (str): search pattern.


    Example:
        GET /browse/search?pattern=python*
        GET /browse/search?lang=java
        GET /browse/search?tag=ml

    Returns:
        A list of projects matching the search criteria.
    """
    arguments = request.args
    arguments = dict(arguments)
    projects = docs_dir_scanner.search_by_filter(**arguments)

    error = None
    if not projects:
        error = f"no projects found matching {arguments}"

    return render_template("browse.html", projects=projects, config=config, error=error, show_search=True)


@display_routes.route("/view/<project>/<version>", methods=["GET"])
def view(project, version):
    """
    View the documentation for a specific project.

    Args:
        project (str): name of the project whose latest version is to be fetched.
        version (str): version of the project to be fetched.

    Example:
        GET /browse/view/<project>/<version>

    Returns:
        Get the latest version of the project.
    """
    info = docs_dir_scanner.get_proj_versions(project)
    specific_path = request.args.get("path", None)

    # if specific_path:
    #     url_parts = f"{config.docfiles_link_root}/{project}/{version,`` specific_path]

    if version in info["versions"]:
        url = "/".join([config.docfiles_link_root, project, version, "index.html"])
        return render_template(
            "view_docs.html", doc_url=url, show_ver_dropdown=True, project_info=info, curr_ver=version
        )

    return jsonify({"error": f"Project {project} not found"}), 404


@display_routes.route("/changelog/<project>", methods=["GET"])
def changelog(project):
    """
    View the changelog if available of a project.

    Args:
        project (str): name of the project whose latest version is to be fetched.

    Example:
        GET /browse/changelog/<project>
    """
    changelog = Path(f"{config.docfiles_dir}/{project}/changelog.html")

    if changelog.exists():
        text = changelog.read_text()
    else:
        text = f"< '{changelog}' missing! >"

    return render_template("changelog.html", content=text)  
