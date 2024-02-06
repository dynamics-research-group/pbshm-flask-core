import json
from datetime import datetime

import click
import pymongo
from flask import Blueprint
from urllib.request import urlopen

from pbshm.db import db_connect

#Constants
REPO_OWNER = "dynamics-research-group"
REPO_NAME = "pbshm-schema"
REPO_RELEASE_FILE = "structure-data-compiled-mongodb.min.json"
GITHUB_RELEASE_LIST = "https://api.github.com/repos/{owner}/{repo}/releases"
GITHUB_RELEASE_LATEST = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
GITHUB_RELEASE_TAG = "https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"

#Create the Mechanic Blueprint
bp = Blueprint("Mechanic", __name__, cli_group="mechanic")

#Available Versions
@bp.cli.command("versions")
def mechanic_available_versions():
    #Load Remote API
    print("Retrieving latest version of PBSHM Schema")
    with urlopen(GITHUB_RELEASE_LIST.format(owner=REPO_OWNER, repo=REPO_NAME)) as response:
        if response.getcode() != 200:
            print("An error occured while trying to retrieve the list of PBSHM Schema Releases")
        else:
            raw = response.read()
            data = json.loads(raw.decode("utf-8"))
            for release in data:
                print("Version: {version}\t\tDate: {date}\t\tAuthor: {author}".format(version=release["tag_name"], date=datetime.fromisoformat(release["published_at"].replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M"), author=release["author"]["login"]))

#Install New Structure Collection
@bp.cli.command("new-structure-collection")
@click.option("--version", default="latest")
@click.argument("collection")
def mechanic_new_collection(version, collection):
    create_new_structure_collection(collection, version)

#Create New Structure Collection
def create_new_structure_collection(collection, version="latest"):
    #Retrieve Asset List
    print("Retrieving list of assets for {version}".format(version=version))
    download_url = ""
    with urlopen(GITHUB_RELEASE_LATEST.format(owner=REPO_OWNER, repo=REPO_NAME) if version == "latest" else GITHUB_RELEASE_TAG.format(owner=REPO_OWNER, repo=REPO_NAME, tag=version)) as response:
        if response.getcode() != 200:
            print("An error occured while trying to retrieve the assets for version: {version} of the PBSHM Schema".format(version=version))
        else:
            raw = response.read()
            data = json.loads(raw.decode("utf-8"))
            #Find the correct Asset
            for asset in data["assets"]:
                if asset["name"] == REPO_RELEASE_FILE:
                    download_url = asset["browser_download_url"]
                    break
    #Ensure Download URL
    if download_url == "":
        print("Sorry, we were unable to find the correct asset for version: {version}".format(version=version))
        return
    #Download Schema
    print("Downloading {version} schema from {url}".format(version=version, url=download_url))
    with urlopen(download_url) as response:
        if response.getcode() != 200:
            print("An error occured while trying to download the PBSHM Schema version: {version}".format(version=version))
        else:
            raw = response.read()
            schema = json.loads(raw.decode("utf-8"))
            print("Installing {version} into {collection}".format(version=version, collection=collection))
            #Create Collection
            db = db_connect()
            db.create_collection(collection, validator={
                "$jsonSchema": schema
            })
            #Create Indexes
            print("Creating default indexes")
            db[collection].create_index([
                ("population", pymongo.ASCENDING),
                ("name", pymongo.ASCENDING),
                ("timestamp", pymongo.ASCENDING),
                ("channels.name", pymongo.ASCENDING)
            ], name="pbshm_framework_channel", unique=True)
    print("Complete")
