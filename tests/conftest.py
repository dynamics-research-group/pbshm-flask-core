import os
import json

from flask import Flask
from flask.testing import FlaskClient
import pymongo
import pytest

from pbshm import create_app

@pytest.hookimpl(tryfirst=True, hookwrapper=False)
def pytest_sessionstart():
    """
    If wanting to run these tests locally you need the json file 
    ./tests/local_test_credentials.json with the credentials to your local
    MongoDB instance. The required form is:
    {
        "MONGODB_HOST" : "localhost",
        "MONGODB_PORT" : "27017",
        "MONGODB_USERNAME" : "YourUserName",
        "MONGODB_PASSWORD" : "YourPassword",
        "MONGODB_AUTH_DB" : "admin",
        "MONGODB_DATA_DB" : "unittest_db",
        "MONGODB_USERS_COLLECTION" : "unittest_users",
        "MONGODB_STRUCTURE_COLLECTION" : "unittest_structures",
        "MONGODB_SECRET_KEY" : "unittest_key",
        "PBSHM_USERNAME" : "user@test.com",
        "PBSHM_PASSWORD" : "1234",
        "PBSHM_FORENAME" : "Test",
        "PBSHM_SURNAME" : "User"
    }
    """
    # Copy the local_test_credentials.json format as outlined in the docstring.
    if os.path.exists("./tests/local_test_credentials.json"):
        with open("./tests/local_test_credentials.json") as f:
            environment_vars = json.load(f)

        for key, val in environment_vars.items():
            if key in os.environ:
                print(f"Overriding environment variable: {key} which had previous value {os.environ[key]}")
            os.environ[key] = val

    # Drop collections that were created from previous test run. If the
    # collection does not exist, the drop method returns False and no error is
    # raised.
    client = pymongo.MongoClient(
        host=os.environ.get("MONGODB_HOST"),
        port=int(os.environ.get("MONGODB_PORT")),
        username=os.environ.get("MONGODB_USERNAME"),
        password=os.environ.get("MONGODB_PASSWORD")
    )
    db = client[os.environ.get("MONGODB_DATA_DB")]
    db[os.environ.get("MONGODB_STRUCTURE_COLLECTION")].drop()
    db[os.environ.get("MONGODB_USERS_COLLECTION")].drop()
    for collection_name in db.list_collection_names():
        if "unittest_" in collection_name:
            db[collection_name].drop()

def pytest_collection_modifyitems(items):
    """
    Modifies test items in place to ensure test modules run in a given order.
    https://stackoverflow.com/questions/17571438/how-to-control-test-case-execution-order-in-pytest
    """
    MODULE_ORDER = [
        "tests.test_initialisation",
        "tests.test_authentication",
        "tests.test_mechanic",
        "tests.test_timekeeper"
    ]
    module_mapping = {item: item.module.__name__ for item in items}

    sorted_items = items.copy()
    # Iteratively move tests of each module to the end of the test queue
    for module in MODULE_ORDER:
        sorted_items = [it for it in sorted_items if module_mapping[it] != module] + [
            it for it in sorted_items if module_mapping[it] == module
        ]
    items[:] = sorted_items

@pytest.fixture()
def app() -> Flask:
    """
    App instance for use in the tests.
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app) -> FlaskClient:
    """
    Test client.
    """
    return app.test_client()

@pytest.fixture
def runner(app) -> FlaskClient:
    """
    Command line client for running command line inputs.
    """ 
    return app.test_cli_runner()

@pytest.fixture
def authenticated_client(client, app) -> FlaskClient:
    """
    Used for creating an authenticated client.
    """
    with app.app_context():
        client.post(
            "/authentication/login",
                data={
                    "email-address": os.environ["PBSHM_USERNAME"],
                    "password": os.environ["PBSHM_PASSWORD"]
                }
            )
        yield client
