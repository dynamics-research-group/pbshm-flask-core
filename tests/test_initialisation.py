import os
import json
from urllib.request import urlopen

import pytest
import pymongo

from tests.auxiliary import user_collection, default_collection

@pytest.mark.dependency()
class TestInitialiseSubSystemConfig:
    @pytest.mark.dependency()
    def test_cli_call(self, runner):
        """
        Tests for successful execution for this initialisation. After this, there should be an instance file.
        """
        test_args = ["init", "config"]
        input_params = [
            os.environ["MONGODB_HOST"],  # Prompt for the database host
            os.environ["MONGODB_PORT"],  # Propmpt for the MongoDB port
            os.environ["MONGODB_AUTH_DB"],  # Prompt for admin database collection
            os.environ["MONGODB_USERNAME"],  # Login to the database with priveleges to create new collections 
            os.environ["MONGODB_PASSWORD"],  # Authentication into the database
            os.environ["MONGODB_PASSWORD"],  # Repeat password
            os.environ["MONGODB_DATA_DB"],  # Database where the user plans to run core/ framework
            os.environ["MONGODB_USERS_COLLECTION"],  # Collection which holds the users to the database
            os.environ["MONGODB_STRUCTURE_COLLECTION"],  # Collection which holds the structure data
            os.environ["MONGODB_SECRET_KEY"]  # Secret key to log in to the database
        ]
        input_params = '\n'.join(input_params)
        result = runner.invoke(args=test_args, input=input_params)
        assert result.output
        assert result.exit_code == 0

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemConfig::test_cli_call"])
    def test_config_file_exists(self):
        """
        Test if the "init config" command has created an instance folder and a
        config.json file inside.
        """
        assert os.path.isdir(os.path.join(os.getcwd(), "instance"))
        assert os.path.isfile(os.path.join(os.getcwd(), "instance", "config.json"))
    
    @pytest.mark.dependency(depends=["TestInitialiseSubSystemConfig::test_config_file_exists"])
    def test_config_contents(self):
        """
        Test that the contents of the config.json file are as expected, given
        command line inputs in TestInitialiseSubSystemConfig::test_cli_call.
        """
        with open(os.path.join(os.getcwd(), "instance", "config.json")) as f:
            config = json.load(f)
        assert config["MONGODB_URI"] == f"mongodb://{os.environ['MONGODB_USERNAME']}:{os.environ['MONGODB_PASSWORD']}@{os.environ['MONGODB_HOST']}:{os.environ['MONGODB_PORT']}/{os.environ['MONGODB_AUTH_DB']}"
        assert config["PBSHM_DATABASE"] == os.environ["MONGODB_DATA_DB"] 
        assert config["USER_COLLECTION"] == os.environ["MONGODB_USERS_COLLECTION"]
        assert config["DEFAULT_COLLECTION"] == os.environ["MONGODB_STRUCTURE_COLLECTION"]
        assert config["SECRET_KEY"] == os.environ["MONGODB_SECRET_KEY"]
    
    @pytest.mark.dependency(depends=["TestInitialiseSubSystemConfig::test_config_file_exists"])
    def test_credentials_successful_connection(self):
        """
        Test whether credentials inside config.json are valid and allow access
        to the database. 
        """
        with open(os.path.join(os.getcwd(), "instance", "config.json")) as f:
            config = json.load(f)
        db = pymongo.MongoClient(config["MONGODB_URI"])[config["PBSHM_DATABASE"]]

        db.create_collection("unittest_throwaway")
        assert len(db.list_collection_names()) > 0
        assert "unittest_throwaway" in db.list_collection_names()
    
    @pytest.mark.dependency(depends=["TestInitialiseSubSystemConfig::test_cli_call"])
    def test_incorrect_credentials_fail(self):
        """
        Test whether wrong credentials do not work. Essentially testing whether
        authentication is properly set up on the database.
        """
        with open(os.path.join(os.getcwd(), "instance", "config.json")) as f:
            config = json.load(f)
        bad_uri = f"mongodb://notAnAdmin:wrongPassword@{os.environ['MONGODB_HOST']}:{os.environ['MONGODB_PORT']}/{os.environ['MONGODB_AUTH_DB']}"
        db = pymongo.MongoClient(bad_uri)[config["PBSHM_DATABASE"]]
        with pytest.raises(pymongo.errors.OperationFailure) as exception_info:
            db.list_collection_names()
        assert exception_info.value.details.get("errmsg") == "Authentication failed."


@pytest.mark.dependency(depends=["TestInitialiseSubSystemConfig"])
class TestInitialiseSubSystemDB:
    @pytest.mark.dependency()
    def test_cli_call(self, runner):
        """
        Tests for successful execution. 
        """
        result = runner.invoke(args=["init", "db"])
        assert result.exit_code == 0

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_cli_call"])
    def test_has_user_collection(self):
        """
        Test whether the user collection has been created.
        """
        assert user_collection() is not None

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_has_user_collection"])
    def test_user_collection_has_schema(self):
        """
        Test whether the user_collection has a schema.
        """
        assert user_collection().options()["validator"]

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_user_collection_has_schema"])
    def test_user_collection_has_correct_schema(self):
        """
        Tests whether the user_collection has the correct schema.
        """
        user_schema = user_collection().options()["validator"]
        with open(os.path.join(os.getcwd(), "pbshm", "initialisation", "user-schema.json"), 'r') as f:
            schema_file = json.load(f)
        assert user_schema["$jsonSchema"] == schema_file

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_cli_call"])
    def test_user_index_email(self):
        """
        Test whether the user collection is indexed by the email address. If
        not, the same email address can be passed in for multiple users.

        'emailAddress_1' is the autogenerated index name in the collection.
        """
        index_info = user_collection().index_information()
        assert index_info
        assert "emailAddress_1" in index_info
        assert index_info["emailAddress_1"]["unique"] == True
    
    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_cli_call"])
    def test_has_default_collection(self):
        """
        Test whether the default collection exists.
        """
        assert default_collection() is not None

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_has_default_collection"])
    def test_default_collection_has_schema(self):
        """
        Test whether the default collection has a schema.
        """
        assert default_collection().options()["validator"]

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemDB::test_default_collection_has_schema"])
    def test_default_collection_has_correct_schema(self):
        """
        Tests whether the default_collection has the correct schema by
        downloading the latest version and equating the two.
        """    
        download_url = ""
        with urlopen("https://api.github.com/repos/dynamics-research-group/pbshm-schema/releases/latest") as response:
            raw = response.read()
            data = json.loads(raw.decode("utf-8"))
            # Find the correct Asset
            for asset in data["assets"]:
                if asset["name"] == "structure-data-compiled-mongodb.min.json":
                    download_url = asset["browser_download_url"]
                    break
        # Download Schema
        with urlopen(download_url) as response:
            raw = response.read()
            structure_schema = json.loads(raw.decode("utf-8"))
        assert default_collection().options()["validator"]["$jsonSchema"] == structure_schema
        
@pytest.mark.dependency(depends=["TestInitialiseSubSystemDB"])
class TestInitialiseSubSystemNewRootUser:
    @pytest.mark.dependency()
    def test_cli_call(self, runner):
        """
        Tests for successful execution.
        """
        test_args = ["init", "new-root-user"]
        input_params = [
            os.environ["PBSHM_USERNAME"],
            os.environ["PBSHM_PASSWORD"],
            os.environ["PBSHM_PASSWORD"],
            os.environ["PBSHM_FORENAME"],
            os.environ["PBSHM_SURNAME"]
        ]
        input_params = '\n'.join(input_params)
        result = runner.invoke(args=test_args, input=input_params)
        assert result.output
        assert result.exit_code == 0
    
    @pytest.mark.dependency(depends=["TestInitialiseSubSystemNewRootUser::test_cli_call"])
    def test_user_in_users(self):
        """
        Check whether the new root user can be found within the user
        collection.
        """
        doc_1 = user_collection().find_one({"emailAddress": os.environ["PBSHM_USERNAME"]})
        doc_2 = user_collection().find_one({"firstName": os.environ["PBSHM_FORENAME"]})
        doc_3 = user_collection().find_one({"secondName": os.environ["PBSHM_SURNAME"]})
        assert doc_1 == doc_2
        assert doc_2 == doc_3

    @pytest.mark.dependency(depends=["TestInitialiseSubSystemNewRootUser::test_cli_call"])
    def test_add_user_same_email(self, runner):
        """
        Try to create a second root user with the same email address as before.
        This test should fail.
        """
        test_args = ["init", "new-root-user"]
        input_params = [
            os.environ["PBSHM_USERNAME"],
            "1234567",
            "1234567",
            "Test2",
            "User2"
        ]
        input_params = '\n'.join(input_params)
        result = runner.invoke(args=test_args, input=input_params)
        # The user with the same email shouldn't have been added.
        users = user_collection().count_documents({"emailAddress": os.environ["PBSHM_USERNAME"]})
        assert result.output
        assert result.exit_code == 1  # Raises an error when adding the same email
        assert users == 1
    
    @pytest.mark.dependency(depends=["TestInitialiseSubSystemNewRootUser::test_cli_call"])
    def test_add_user_same_name(self, runner):
        """
        Add a user with everything the same, except for email address. This
        test should pass.
        """
        test_args = ["init", "new-root-user"]
        input_params = [
            "user2@test.com",
            os.environ["PBSHM_PASSWORD"],
            os.environ["PBSHM_PASSWORD"],
            os.environ["PBSHM_FORENAME"],
            os.environ["PBSHM_SURNAME"]
        ]
        input_params = '\n'.join(input_params)
        result = runner.invoke(args=test_args, input=input_params)
        users = user_collection().count_documents({})
        assert result.output
        assert result.exit_code == 0  # Doesn't raise an error when adding the same name
        assert users == 2  # The user with the same email shouldn't have been added.