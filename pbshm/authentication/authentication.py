from functools import wraps

from bson import ObjectId
from flask import Blueprint, g, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash

from pbshm.db import user_collection

#Create the Authentication Blueprint
bp = Blueprint("authentication", __name__, template_folder="templates")

#Login View
@bp.route("/login", methods=("GET", "POST"))
def login():
    #Handle Request
    error = None
    if(request.method == "POST"):
        #Validate Inputs
        email_address = request.form["email-address"]
        password = request.form["password"]
        if not email_address: error = "Missing email address."
        elif not password: error = "Missing password."
        #Process Request if no error
        if error is None:
            user = user_collection().find_one(
                { "emailAddress": email_address },
                { "_id": 1, "password": 1, "enabled": 1}
            )
            if user is None: error = "Unable to locate these credentials."
            elif not user["enabled"]: error = "This account has been disabled."
            elif not check_password_hash(user["password"], password): error = "This email address and password do not match any credentials."
            else:
                session.clear()
                session["user_id"] = str(user["_id"])
                return redirect("/")
    #Render Login Template
    return render_template("login.html", error=error)

#Logout View
@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#Load User Data into Global from Session
@bp.before_app_request
def load_user_data():
    user_id = session.get("user_id")
    if user_id is None: g.user = None
    else:
        user = user_collection().find_one(
            { "_id": ObjectId(user_id) },
            { "_id": 1, "firstName": 1, "secondName": 1 }
        )
        g.user = { "_id": str(user["_id"]), "firstName": user["firstName"], "secondName": user["secondName"] }

#Authenticate Request
def authenticate_request(permission=None):
    def view_decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None: return redirect(url_for("authentication.login"))
            else:
                user = user_collection().find_one(
                    { "_id": ObjectId(g.user["_id"]), "enabled": True } if permission is None else { "_id": ObjectId(g.user["_id"]), "enabled": True, "permissions": { "$in": [permission, "root"] } },
                    { "_id": 1 }
                )
                if user is None or g.user["_id"] != str(user["_id"]): return redirect(url_for("authentication.login", reason="denied"))
            return view(*args, **kwargs)
        return wrapped
    return view_decorator