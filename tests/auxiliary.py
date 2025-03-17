import os
import json

import pymongo

def get_config():
    """
    For returning the configuration details from the instance folder.
    """
    with open(os.path.join(os.getcwd(), "instance", "config.json")) as f:
        config = json.load(f)
    return config

def db_connect():
    """
    Helper function for connecting to the database.
    """
    config = get_config()
    return pymongo.MongoClient(config["MONGODB_URI"])[config["PBSHM_DATABASE"]]

def user_collection():
    """
    Helper function for connecting to the user collection.
    """
    config = get_config()
    return db_connect()[config["USER_COLLECTION"]]

def default_collection():
    """
    Helper function for connecting to the default structure collection.
    """
    config = get_config()
    return db_connect()[config["DEFAULT_COLLECTION"]]


def response_code_successful(response):
    """
    Helper function to sort HTTP response status codes.
        0 = fail
        1 = successful
        2 = redirect
    """
    if 200 <= response.status_code < 300:
        return 1
    elif 300 <= response.status_code < 400:
        return 2
    else:
        return 0

