from functools import wraps
import hashlib
import hmac

from bson import ObjectId
from flask import Blueprint, g, render_template, request, session, redirect, url_for, current_app
from werkzeug.exceptions import Unauthorized
from werkzeug.security import generate_password_hash

from pbshm.db import user_collection

#Create the Authentication Blueprint
bp = Blueprint("authentication", __name__, template_folder="templates")

DEFAULT_PBKDF2_ITERATIONS = 600000


def _drg_hash_internal(method, salt, password):
    """
    A modified version of Werkzeug's '_hash_internal', extended to support 
    SHA3_512 for legacy purposes. Taken from Werkzeug source code (version < 2.4).
    Deprecated hash algorithms return "DEPRECATED" to signal the need for a
    hash update, instead of the usual method and parameters.
    """
    method, *args = method.split(":")
    salt_bytes = salt.encode()
    password_bytes = password.encode()

    if method == "scrypt":
        if not args:
            n = 2**15
            r = 8
            p = 1
        else:
            try:
                n, r, p = map(int, args)
            except ValueError:
                raise ValueError("'scrypt' takes 3 arguments.") from None

        maxmem = 132 * n * r * p  # ideally 128, but some extra seems needed
        return (
            hashlib.scrypt(
                password_bytes, salt=salt_bytes, n=n, r=r, p=p, maxmem=maxmem
            ).hex(),
            f"scrypt:{n}:{r}:{p}",
        )
    
    elif method == "pbkdf2":
        len_args = len(args)

        if len_args == 0:
            hash_name = "sha256"
            iterations = DEFAULT_PBKDF2_ITERATIONS
        elif len_args == 1:
            hash_name = args[0]
            iterations = DEFAULT_PBKDF2_ITERATIONS
        elif len_args == 2:
            hash_name = args[0]
            iterations = int(args[1])
        else:
            raise ValueError("'pbkdf2' takes 2 arguments.")

        return (
            hashlib.pbkdf2_hmac(
                hash_name, password_bytes, salt_bytes, iterations
            ).hex(),
            f"pbkdf2:{hash_name}:{iterations}",
        )
    
    else:
        return (
            hmac.new(salt_bytes, password_bytes, method).hexdigest(),
            "DEPRECATED"
        )


def drg_check_password_hash(pwhash, password):
    """
    Verifies if the password matches the given hash (pwhash). 
    Returns two booleans: the first indicates if the passwords match, and the 
    second indicates if the hash requires updating.
    """
    method, salt, hashval = pwhash.split('$', 2)
    hashed_pw, method = _drg_hash_internal(method, salt, password)
    
    passwords_match = hmac.compare_digest(hashed_pw, hashval)
    # Even if the hash needs updating, the hash is not updated because the
    # passwords do not match! This is an absolute fail safe as the update
    # actually happens inside a conditional only if the passwords match, but
    # better to be safe than sorry!
    needs_updating = (method == "DEPRECATED") if passwords_match else False

    return passwords_match, needs_updating


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
            passwords_match, needs_updating = drg_check_password_hash(user["password"], password)
            if user is None:
                error = "Unable to locate these credentials."
            elif not user["enabled"]:
                error = "This account has been disabled."
            elif not passwords_match:
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