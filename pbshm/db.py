import pymongo
from flask import current_app, g

#Connect
def db_connect():
    if "db" not in g:
        g.db = pymongo.MongoClient(current_app.config["MONGODB_URI"])[current_app.config["PBSHM_DATABASE"]]
    return g.db

#User Collection
def user_collection():
    if "user_collection" not in g:
        g.user_collection = db_connect()[current_app.config["USER_COLLECTION"]]
    return g.user_collection

#Default Collection
def default_collection():
    if "default_collection" not in g:
        g.default_collection = db_connect()[current_app.config["DEFAULT_COLLECTION"]]
    return g.default_collection