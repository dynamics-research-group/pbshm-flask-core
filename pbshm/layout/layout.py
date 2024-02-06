from flask import Blueprint, g, render_template, jsonify

from pbshm.authentication import authenticate_request
from pbshm.db import default_collection

#Create the layout Blueprint
bp = Blueprint(
    "layout",
    __name__,
    static_folder = "static",
    template_folder = "templates"
)

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