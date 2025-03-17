import json
import os
from urllib.request import urlopen

import pymongo
import pytest

# Global variables needed for tests.
uri = f"mongodb://{os.environ['MONGODB_USERNAME']}:{os.environ['MONGODB_PASSWORD']}@{os.environ['MONGODB_HOST']}:{os.environ['MONGODB_PORT']}/{os.environ['MONGODB_AUTH_DB']}"
db = pymongo.MongoClient(uri)[os.environ["MONGODB_DATA_DB"]]

# Load all the current schema versions in global scope, as multiple calls to
# the github api causes rate limiting.
all_schema_versions = []
with urlopen("https://api.github.com/repos/dynamics-research-group/pbshm-schema/releases") as response:
    raw = response.read()
    data = json.loads(raw.decode("utf-8"))
    for version in data:
        # Stores the version numbers in a list from newest to oldest.
        all_schema_versions.append(version["tag_name"])

class TestMechanicAvailableVersions:
    @pytest.mark.dependency()
    def test_cli_call(self, runner):
        """
        Tests for successful execution.
        """
        test_args = ["mechanic", "versions"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 0
        assert result.output
    
    @pytest.mark.dependency(depends=["TestMechanicAvailableVersions::test_cli_call"])
    def test_number_of_versions_printed(self, runner):
        """
        Check the output is equivalent to the most recent version.
        """
        test_args = ["mechanic", "versions"]
        result = runner.invoke(args=test_args)

        output_version_numbers = []
        for line in result.output.split('\n'):        
            if "Version: " in line:
                version_length = len("Version: ")
                date_index = line.index("Date: ")
                version_number = line[version_length: date_index].strip()
                output_version_numbers.append(version_number)

        assert len(all_schema_versions) == len(output_version_numbers)
        assert sorted(all_schema_versions) == sorted(output_version_numbers)


class TestMechanicNewCollection:
    @pytest.mark.dependency()    
    def test_cli_call(self, runner):
        """
        Tests for successful execution.
        """
        test_args = ["mechanic", "new-structure-collection", "unittest_new_collection"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 0
        assert result.output

    @pytest.mark.dependency(depends=["TestMechanicNewCollection::test_cli_call"])
    def test_latest_version_collection_created(self):
        """
        Test if we can find the new collection just created, under the name
        'unittest_new_collection'. The latest schema version is passed as
        default.
        """     
        assert db["unittest_new_collection"] is not None
        assert db["unittest_new_collection"].options()["validator"]
        assert db["unittest_new_collection"].options()["validator"]["$jsonSchema"]["properties"]["version"]["enum"] == [all_schema_versions[0][1:]]  # Assert this is the most recent version.

    @pytest.mark.dependency(depends=["TestMechanicNewCollection::test_latest_version_collection_created"])
    def test_latest_version_same_collection_name_blocked(self, runner):
        """
        Test if a collection is created with a name that already exists, then
        the command fails.
        """
        test_args = ["mechanic", "new-structure-collection", "unittest_new_collection"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 1
        assert result.output

    @pytest.mark.dependency(depends=["TestMechanicNewCollection::test_latest_version_same_collection_name_blocked"])
    def test_latest_version_same_collection_schema_exists_after_fail(self):
        """
        Ensure that the schema has not been altered upon the failure from the
        previous test.
        """
        assert db["unittest_new_collection"] is not None
        assert db["unittest_new_collection"].options()["validator"]["$jsonSchema"]

    @pytest.mark.dependency()
    def test_legacy_version_creation(self, runner):
        """
        Check old version of the schema is loaded in to the collection.
        The schema version 1.0.1 did not have a version tag inside the schema,
        and this tests leverages that fact.
        """
        test_args = ["mechanic", "new-structure-collection", "unittest_legacy_schema", "--version", "v1.0.1"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 0
        assert result.output
        assert "version" not in db["unittest_legacy_schema"].options()["validator"]["$jsonSchema"]["properties"]

    @pytest.mark.dependency(depends=["TestMechanicNewCollection::test_legacy_version_creation"])
    def test_legacy_version_same_collection_name_blocked(self, runner):
        """
        Test if multiple calls of creating a new collection with a legacy
        schema is blocked.
        """
        test_args = ["mechanic", "new-structure-collection", "unittest_legacy_schema", "--version", "v1.0.1"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 1
        assert result.output
    
    @pytest.mark.dependency(depends=["TestMechanicNewCollection::test_legacy_version_same_collection_name_blocked"])
    def test_legacy_version_into_latest_version_collection_blocked(self, runner):
        """
        If a structure collection already exists with schema x and then someone
        tries to create a collection with the same name and a different schema
        y. The schema version should remain as x.
        """
        test_args = ["mechanic", "new-structure-collection", "unittest_new_collection", "--version", "v1.0.1"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 1
        assert result.output

        assert "version" in db["unittest_new_collection"].options()["validator"]["$jsonSchema"]["properties"]
        assert db["unittest_new_collection"].options()["validator"]["$jsonSchema"]["properties"]["version"]["enum"] == [all_schema_versions[0][1:]]

    def test_nonexistent_version_blocking(self, runner):
        """
        Check a nonexistent schema version is not installed and cli call
        results in error. The first version was 1.0, therefore, anything
        before this should fail.
        """
        test_args = ["mechanic", "new-structure-collection", "unittest_nonexistent_schema", "--version", "v0.1"]
        result = runner.invoke(args=test_args)
        assert result.exit_code == 1
        assert result.output
        assert "unittest_nonexistent_schema" not in db.list_collection_names()