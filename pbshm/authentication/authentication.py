from functools import wraps
import hashlib
import hmac

from bson import ObjectId
from flask import Blueprint, g, render_template, request, session, redirect, url_for, current_app
from werkzeug.exceptions import Unauthorized
from werkzeug.security import generate_password_hash, check_password_hash

from pbshm.db import user_collection

#Create the Authentication Blueprint
bp = Blueprint("authentication", __name__, template_folder="templates")


def generate_password_hash_sha3_512(method, salt, password):
    """
    Hash function for SHA3_512 for legacy purposes.
    """
    salt_bytes = salt.encode()
    password_bytes = password.encode()
    return hmac.new(salt_bytes, password_bytes, method).hexdigest()


def check_password_hash_includes_sha3(pwhash, password):
    """
    Verifies if the password matches the given hash (pwhash). 
    Returns two booleans: the first indicates if the passwords match, and the 
    second indicates if the hash requires updating.
    """
    method, salt, hashval = pwhash.split('$', 2)
    if method == "sha3_512":
        hashed_pw = generate_password_hash_sha3_512(method, salt, password)
        passwords_match = hmac.compare_digest(hashed_pw, hashval)
        return passwords_match, True
    else:
        return (check_password_hash(pwhash, password), False)


#Login View
@bp.route("/login", methods=("GET", "POST"))
def login():
    #Handle Request
    error = None
    if (request.method == "POST"):
        #Validate Inputs
        email_address = request.form["email-address"]
        password = request.form["password"]
        if not email_address: error = "Missing email address."
        elif not password: error = "Missing password."
        #Process Request if no error
        if error is not None:
            return render_template("login.html", error=error)
        
        user = user_collection().find_one(
            { "emailAddress": email_address },
            { "_id": 1, "password": 1, "enabled": 1}
        )
        if user is None:
            error = "Unable to locate these credentials."
        elif not user["enabled"]:
            error = "This account has been disabled."
        if error is not None:
            return render_template("login.html", error=error)
        
        passwords_match, needs_updating = check_password_hash_includes_sha3(user["password"], password)
        if not passwords_match:
            error = "This email address and password do not match any credentials."
        else:
            if needs_updating:
                user_collection().update_one(
                    {"_id": user["_id"]},
                    {"$set": {"password": generate_password_hash(password, method="scrypt:32768:8:1", salt_length=128)}}
                )
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
            if g.user is None: raise Unauthorized(description="Please login to perform this action")
            else:
                user = user_collection().find_one(
                    { "_id": ObjectId(g.user["_id"]), "enabled": True } if permission is None else { "_id": ObjectId(g.user["_id"]), "enabled": True, "permissions": { "$in": [permission, "root"] } },
                    { "_id": 1 }
                )
                if user is None or g.user["_id"] != str(user["_id"]): raise Unauthorized(description="You do not have permission to perform this action")
            return view(*args, **kwargs)
        return wrapped
    return view_decorator


def handle_unauthorised_request(e):
    """
    Error handler function for 401 HTTP status code.
    """
    if current_app.config["TESTING"] == False:
        return redirect(url_for("authentication.login"))
    else:
        return e