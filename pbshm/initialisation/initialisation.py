import json
from os import urandom, makedirs
from os.path import isdir, join

import click
import pymongo
from flask import Blueprint, current_app
from urllib.parse import quote_plus
from werkzeug.security import generate_password_hash

from pbshm.db import db_connect
from pbshm.mechanic import create_new_structure_collection

#Create the Initialisation Blueprint
bp = Blueprint("initialisation", __name__, cli_group="init")
bp.cli.chain = True

#Initialise Sub System: Config
@bp.cli.command("config")
@click.option("--hostname", prompt="Hostname", default="localhost")
@click.option("--port", prompt="Port", type=int, default=27017)
@click.option("--authentication-database", prompt="Authentication database", default="admin")
@click.option("--database-username", "username", prompt="Database username")
@click.option("--database-password", "password", prompt="Database password", hide_input=True, confirmation_prompt=True)
@click.option("--pbshm-database", prompt="PBSHM database", default="drg-pbshm")
@click.option("--user-collection", prompt="Users collection", default="users")
@click.option("--default-collection", prompt="Default data collection", default="structures")
@click.option("--secret-key", prompt="Secret Key", default="")
def initialise_sub_system_config(
    hostname, port, authentication_database, username, password,
    pbshm_database, user_collection, default_collection, secret_key
):
    #Create Config Dictionary
    config = {
        "MONGODB_URI": 'mongodb://{username}:{password}@{hostname}:{port}/{authentication_database}'.format(
            username=quote_plus(username), password=quote_plus(password),
            hostname=hostname, port=port, authentication_database=authentication_database
        ),
        "PBSHM_DATABASE": pbshm_database,
        "USER_COLLECTION": user_collection,
        "DEFAULT_COLLECTION": default_collection,
        "SECRET_KEY": str(urandom(32)) if not secret_key else secret_key
    }
    #Write Config File
    if not isdir(current_app.instance_path): makedirs(current_app.instance_path) 
    with open(join(current_app.instance_path, "config.json"), "w") as file:
        json.dump(config, file)
    

#Initialise Sub System: DB
@bp.cli.command("db")
def initialise_sub_system_db():
    #Create Structure Collection
    create_new_structure_collection(current_app.config["DEFAULT_COLLECTION"])
    #Load Schema File
    with current_app.open_resource("initialisation/user-schema.json") as file:
        schema = json.load(file)
    #Create User Collection
    db = db_connect()
    db.create_collection(current_app.config["USER_COLLECTION"], validator={
        "$jsonSchema": schema
    })
    db[current_app.config["USER_COLLECTION"]].create_index(
        [("emailAddress", pymongo.ASCENDING)], unique=True
    )

#Initialise Sub System: New Root User
@bp.cli.command("new-root-user")
@click.option("--email-address", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--first-name", prompt="Your first name")
@click.option("--second-name", prompt="Your second name")
def initialise_sub_system_new_root_user(email_address, password, first_name, second_name):
    #Add In New User with Root Permissions
    db = db_connect()
    db[current_app.config["USER_COLLECTION"]].insert_one({
        "emailAddress": email_address,
        "password": generate_password_hash(password, "sha3_512", 128),
        "firstName": first_name,
        "secondName": second_name,
        "permissions": ["root"],
        "enabled": True
    })
