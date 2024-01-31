import os
import json
from flask import Flask

def create_app(test_config=None):
    #Create Flask App
    app = Flask(__name__, instance_relative_config=True)

    #Load Configuration
    app.config.from_mapping(
        PAGE_SUFFIX=" - PBSHM Core",
        LOGIN_MESSAGE="Welcome to the Dynamics Research Group PBSHM Core, please enter your authentication credentials below.",
        FOOTER_MESSAGE="PBSHM Core, © Dynamics Research Group 2022",
        NAVIGATION={
            "modules":{
                "Pathfinder": "pathfinder.population_list"
            }
        }
    )
    app.config.from_file("config.json", load=json.load, silent=True) if test_config is None else app.config.from_mapping(test_config)

    #Ensure Instance Folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #Add Blueprints
    ## Initialisation
    from pbshm.initialisation import initialisation
    app.register_blueprint(initialisation.bp)
    ## Mechanic
    from pbshm.mechanic import mechanic
    app.register_blueprint(mechanic.bp)
    ## Layout
    from pbshm.layout import layout
    app.register_blueprint(layout.bp, url_prefix="/layout")
    ## Authentication
    from pbshm.authentication import authentication
    app.register_blueprint(authentication.bp, url_prefix="/authentication")
    ## Pathfinder
    from pbshm.pathfinder import pathfinder
    app.register_blueprint(pathfinder.bp, url_prefix="/pathfinder")

    #Set Root Page
    app.add_url_rule("/", endpoint="pathfinder.population_list")

    #Return App
    return app