import os
import json

from flask import Flask

from pbshm import authentication, initialisation, layout, mechanic, timekeeper

def create_app(test_config=None):
    #Create Flask App
    app = Flask(__name__, instance_relative_config=True)

    #Load Configuration
    app.config.from_mapping(
        PAGE_SUFFIX=" - PBSHM Core",
        LOGIN_MESSAGE="Welcome to the Dynamics Research Group PBSHM Core, please enter your authentication credentials below.",
        FOOTER_MESSAGE="PBSHM Core © Dynamics Research Group 2022 - 2024",
        NAVIGATION={
            "modules":{
                "Home": "layout.home"
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
    app.register_blueprint(initialisation.bp) ## Initialisation
    app.register_blueprint(mechanic.bp) ## Mechanic
    app.register_blueprint(layout.bp, url_prefix="/layout") ## Layout
    app.register_blueprint(timekeeper.bp, url_prefix="/timekeeper") ## Timekeeper
    app.register_blueprint(authentication.bp, url_prefix="/authentication") ## Authentication
    
    #Set Root Page
    app.add_url_rule("/", endpoint="layout.home")

    #Return App
    return app