import os

from flask import session, g
import pytest

from pbshm.db import user_collection
from tests.auxiliary import user_collection, response_code_successful

unauthenticated_response_code = 401  # HTTP unauthorised error code.
secure_diagnostics = "layout/diagnostics"  # A secure view which returns unauthorised error code if insufficient permissions.

class TestLogin:
    @pytest.mark.dependency()
    def test_login_loads(self, client):
        """
        Testing to see if the root page accessible. This is basically to ensure
        the setup is correct, a test for the tests as it were.
        """
        response = client.get("/authentication/login")
        assert response_code_successful(response) == 1
        assert b"<title>Login - PBSHM Core</title>" in response.data

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_authenticated_fixture(self, authenticated_client):
        """
        After successful login, make sure the user_id is stored within the
        session. 
        """
        with authenticated_client.session_transaction() as session:
            document = user_collection().find_one(
                {"emailAddress": os.environ.get("PBSHM_USERNAME")},
                {"_id": 1, "emailAddress": 1}
            )
            assert "user_id" in session
            assert os.environ.get("PBSHM_USERNAME") == document["emailAddress"]
            assert session["user_id"] == str(document["_id"])

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_correct_credentials(self, client):
        """
        Test with correct credentials, should be redirected to home page.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": os.environ.get("PBSHM_USERNAME"),
                    "password": os.environ.get("PBSHM_PASSWORD")
                }
            )
            document = user_collection().find_one(
                {"emailAddress": os.environ.get("PBSHM_USERNAME")},
                {"_id": 1, "emailAddress": 1}
            )
            assert response_code_successful(response) >= 1
            assert "user_id" in session
            assert os.environ.get("PBSHM_USERNAME") == document["emailAddress"]
            assert session["user_id"] == str(document["_id"])

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_wrong_email_address(self, client):
        """
        Test with wrong email, should be redirected to login page.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": "not-a-user@test.com",
                    "password": os.environ.get("PBSHM_PASSWORD")
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_wrong_password(self, client):
        """
        Test with wrong password, should be redirected to login page.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": os.environ.get("PBSHM_USERNAME"),
                    "password": "incorrect-password"
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code
    
    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_wrong_email_and_password(self, client):
        """
        Test with wrong email and password, should be redirected to login page.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": "not-a-user@test.com",
                    "password": "incorrect-password"
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_no_email_address(self, client):
        """
        Test that an error is raised if no email address is supplied.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": "",
                    "password": os.environ["PBSHM_PASSWORD"]
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_no_password(self, client):
        """
        Test that an error is raised if no password is supplied.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": os.environ["PBSHM_USERNAME"],
                    "password": ""
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_no_username_and_password(self, client):
        """
        Test that an error is raised if no password and username are supplied.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": "",
                    "password": ""
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code

    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_space_email_address(self, client):
        """
        Test that an error is raised if space email address is supplied.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": " ",
                    "password": os.environ["PBSHM_PASSWORD"]
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code
    
    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_space_password(self, client):
        """
        Test that an error is raised if space password is supplied.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": os.environ["PBSHM_USERNAME"],
                    "password": " "
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code
    
    @pytest.mark.dependency(depends=["TestLogin::test_login_loads"])
    def test_space_username_and_password(self, client):
        """
        Test that an error is raised if space password and username are supplied.
        """
        with client:
            response = client.post(
                "authentication/login",
                data={
                    "email-address": " ",
                    "password": " "
                }
            )
            id_in_session = "user_id" in session
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            assert response_code_successful(response) >= 1
            assert not id_in_session
            assert failed_response.status_code == unauthenticated_response_code
    
    @pytest.mark.dependency(depends=["TestLogin::test_correct_credentials"])
    def test_user_disabled(self, client):
        """
        Test that a disabled user cannot access framework.
        """
        with client:
            user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"enabled": False}})
            response = client.post(
                "authentication/login",
                data={
                    "email-address": os.environ.get("PBSHM_USERNAME"),
                    "password": os.environ.get("PBSHM_PASSWORD")
                }
            )
            failed_response = client.get(
                secure_diagnostics,
                follow_redirects=False
            )
            user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"enabled": True}})
            assert response_code_successful(response) == 1
            assert "user_id" not in session
            assert failed_response.status_code == unauthenticated_response_code

class TestLogout:
    @pytest.mark.dependency()
    def test_logout_loads(self, client):
        """
        Testing to see if the root page accessible. This is basically to ensure
        the setup is correct, a test for the tests as it were.
        """
        response = client.get("/authentication/logout")
        assert response_code_successful(response) == 2

    @pytest.mark.dependency(depends=["TestLogout::test_logout_loads"])   
    def test_logout_clears_session(self, client):
        """
        Test whether the session data is cleared upon logging out.
        """
        with client:
            response1 = client.post(
                "authentication/login",
                data={
                    "email-address": os.environ.get("PBSHM_USERNAME"),
                    "password": os.environ.get("PBSHM_PASSWORD")
                }
            )
            id_in_session = "user_id" in session
            response2 = client.get("authentication/logout", follow_redirects=True)
            assert response_code_successful(response1) >= 1
            assert id_in_session
            assert "user_id" not in session

    # @pytest.mark.dependency(depends=["TestLogout::test_logout_loads", "TestLogin::test_authenticated_fixture"])   
    # def test_logout_redirect(self, authenticated_client):
    #     """
    #     Test whether the user is redirected to the login page after logging
    #     out.
    #     """
    #     response1 = authenticated_client.get("authentication/logout", follow_redirects=True)
    #     # Test whether you can access authorised URLs after logging out.
    #     response2 = authenticated_client.get(secure_diagnostics, follow_redirects=True)
    #     assert response_code_successful(response1)
    #     assert response1.request.path == "/authentication/login"
    #     assert response_code_successful(response2)
    #     assert response2.request.path == "/authentication/login"
        

class TestLoadUserData:
    @pytest.mark.dependency(depends=["TestLogin::test_authenticated_fixture"])
    def test_user_in_global(self, app, authenticated_client):
        """
        Test data is loaded into flask.g when calling load_user_data().
        """
        document = user_collection().find_one(
            {"emailAddress": os.environ.get("PBSHM_USERNAME")},
            {"_id": 1, "firstName": 1, "secondName": 1}
        )

        with app.app_context(), authenticated_client:
            authenticated_client.get(secure_diagnostics)  # make request to call load_user_data via its decorator bp.before_app_request
            assert "user" in g
            assert g.user["firstName"] == os.environ["PBSHM_FORENAME"]
            assert g.user["secondName"] == os.environ["PBSHM_SURNAME"]
            assert g.user["firstName"] == document["firstName"]
            assert g.user["secondName"] == document["secondName"]


class TestAuthenticateRequest:
    def no_permission_view(self):
        """
        A function to help tests. This mimics and view that does not require
        any special authentication to access.
        """
        return True
    
    def test_no_user_no_permission(self, app, client):
        """
        No user in global scope so redirected to login page, even if no permission.
        """
        with app.app_context(), client:
            assert self.no_permission_view()

    def test_no_user_with_permission(self, app, client):
        """
        Test when there is no user in the global scope. This should redirect to
        the login page.
        """
        with app.app_context(), client:
            response = client.get(secure_diagnostics, follow_redirects=False)
            assert response.status_code == unauthenticated_response_code

    def test_root_user_with_permission_required(self, authenticated_client):
        """
        Test whether a root user can access a route wrapped with
        authenticate_request() and a permission set. Root user should be able
        to access.
        """
        with authenticated_client:
            response = authenticated_client.get(secure_diagnostics, follow_redirects=False)
            assert response_code_successful(response) >= 1

    def test_standard_user_no_permission(self, authenticated_client):
        """
        Test whether a standard user can access a view which it is not
        authenticated for (user has no permissions).
        """
        user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"permissions": []}})
        with authenticated_client:
            response = authenticated_client.get(secure_diagnostics, follow_redirects=False)
            user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"permissions": ["root"]}})
            assert response.status_code == unauthenticated_response_code
        
    def test_standard_user_wrong_permission(self, authenticated_client):
        """
        Test whether a standard user can access a view which it is not
        authenticated for.
        """
        user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"permissions": ["you-shall-not-pass"]}})
        with authenticated_client:
            response = authenticated_client.get(secure_diagnostics, follow_redirects=False)
            user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"permissions": ["root"]}})
            assert response.status_code == unauthenticated_response_code

    def test_standard_user_with_permission(self, authenticated_client):
        """
        Test whether a standard user can access a view which it is
        authenticated for.
        """
        user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"permissions": ["layout-diagnostics"]}})
        with authenticated_client:
            response = authenticated_client.get(secure_diagnostics, follow_redirects=False)
            user_collection().update_one({"emailAddress": os.environ.get("PBSHM_USERNAME")}, {"$set": {"permissions": ["root"]}})
            assert response_code_successful(response) >= 1
