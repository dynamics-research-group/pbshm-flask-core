from flask import Blueprint, g, render_template
from pbshm.authentication.authentication import authenticate_request

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