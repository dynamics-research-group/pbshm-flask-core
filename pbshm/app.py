import os
import json
from typing import Mapping, Any

from flask import Flask, Blueprint
from werkzeug.exceptions import Unauthorized

from pbshm import authentication, initialisation, layout, mechanic, timekeeper


def create_app(
    test_config: Mapping[str, Any] | None = None,
    layout_blueprint: Blueprint | None = layout.bp,
    root_endpoint: str | None = "layout.home",
):
    # Create Flask App
    app = Flask(__name__, instance_relative_config=True)

    # Load Configuration
    app.config.from_mapping(
        PAGE_SUFFIX="",
        LOGIN_MESSAGE="Welcome to the Dynamics Research Group PBSHM Core, please enter your authentication credentials below.",
        FOOTER_MESSAGE="PBSHM Core © Dynamics Research Group 2022 - 2026",
        NAVIGATION_MODE="text",
        NAVIGATION=[
            {
                "title": "Modules",
                "items": (
                    [{"title": "Home", "endpoint": root_endpoint}]
                    if root_endpoint is not None
                    else []
                ),
            }
        ],
    )
    (
        app.config.from_file("config.json", load=json.load, silent=True)
        if test_config is None
        else app.config.from_mapping(test_config)
    )

    # Ensure Instance Folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Add Functionality Blueprints
    app.register_blueprint(initialisation.bp)  ## Initialisation
    app.register_blueprint(mechanic.bp)  ## Mechanic
    app.register_blueprint(timekeeper.bp, url_prefix="/timekeeper")  ## Timekeeper
    app.register_blueprint(authentication.bp, url_prefix="/authentication")  ## Authentication

    # Register Exceptions
    app.register_error_handler(Unauthorized, authentication.handle_unauthorised_request)

    # Add Layout Blueprint
    if layout_blueprint is not None:
        app.register_blueprint(layout_blueprint, url_prefix="/layout")

    # Set Root Page
    if root_endpoint is not None:
        app.add_url_rule("/", endpoint=root_endpoint)

    # Return App
    return app
