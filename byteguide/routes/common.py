""" Common routes for the byteguide. """
from flask import Blueprint, current_app, jsonify, render_template

from byteguide.config import get_instance_config

common_routes = Blueprint("common", __name__, template_folder="templates")


@common_routes.route("/", methods=["GET"])
def home():
    """Return the landing page."""
    return render_template("landing.html", config=get_instance_config(), show_nav_bar_links=True)


@common_routes.route("/url_map", methods=["GET"])
def url_map():
    """Returns a JSON object containing all the routes in the app."""

    paths = []
    for rule in current_app.url_map.iter_rules():
        paths.append(str(rule))

    return jsonify({"url_map": paths})


@common_routes.route("/faq", methods=["GET"])
def faq():
    """Return a document about how to get started with ByteGuide"""
    return render_template("faq.html", config=get_instance_config(), show_nav_bar_links=True)
