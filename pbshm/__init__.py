import os
from flask import Flask

def create_app(test_config=None):
    #Create Flask App
    app = Flask(__name__, instance_relative_config=True)

    #Load Configuration
    app.config.from_mapping(
        PAGE_SUFFIX=" - PBSHM Flask Core",
        LOGIN_MESSAGE="Welcome to the Dynamics Research Group PBSHM Flask Core, please enter your authentication credentials below.",
        FOOTER_MESSAGE="PBSHM Flask Core V1.0.2, © Dynamics Research Group 2020",
        NAVIGATION={
            "modules":{
                "Pathfinder": "pathfinder.population_list"
            }
        }
    )
    app.config.from_json("config.json", silent=True) if test_config is None else app.config.from_mapping(test_config)
    
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