from flask import Blueprint, g, render_template, jsonify, current_app

from pbshm.authentication import authenticate_request
from pbshm.db import default_collection

# Create the layout Blueprint
bp = Blueprint(
    "layout",
    __name__,
    static_folder = "static",
    template_folder = "templates"
)

def config_option(options_key, default=""):
    key_path = options_key.upper().split(".")
    if len(key_path) > 0 and key_path[0] == "OPTIONS":
        key_path.pop(0)
    branch = current_app.config["OPTIONS"] if "OPTIONS" in current_app.config else {}
    for part in key_path:
        if part not in branch:
            return default
        branch = branch[part]
    return branch if branch else default

def navigation_parameters(parameters: dict) -> dict:
    return {
        key: parameters[key]
        for key in parameters.keys()
        if key not in ["sprite_id", "title", "endpoint"]
    }

@bp.record_once
def register_functions(state):
    state.app.jinja_env.globals["config_option"] = config_option
    state.app.jinja_env.globals["navigation_parameters"] = navigation_parameters

@bp.route("/home")
@authenticate_request("layout-home")
def home():
    if g.user is None: raise Exception("No user data in global object")
    else:
        return render_template("home.html", name=g.user["firstName"])

@bp.route("/diagnostics")
@authenticate_request("layout-diagnostics")
def diagnostics():
    populations = {}
    for document in default_collection().aggregate([
        {"$project":{
            "_id":1,
            "name":1,
            "population":1
        }},
        {"$group":{
            "_id":"$population",
            "structures":{"$addToSet":"$name"}
        }},
        {"$project":{
            "_id":0,
            "population":"$_id",
            "structures":1
        }}
    ]):
        populations[document["population"]] = document["structures"]
    return jsonify({"status":f"Total populations found {len(populations)}, with a total of {sum([len(populations[population]) for population in populations])} unique structures", "details":populations})
