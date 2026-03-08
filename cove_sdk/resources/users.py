from cove_sdk._http import HTTPClient
from cove_sdk.models import Token, User


class UsersClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def login(self, username: str, password: str) -> Token:
        """POST /users/token (form-encoded)."""
        response = self._http.request(
            "POST",
            "/users/token",
            data={"username": username, "password": password, "grant_type": "password"},
        )
        return Token.model_validate(response.json())

    def create(self, username: str, password: str) -> User:
        """POST /users/?username={username}&password={password}."""
        response = self._http.request(
            "POST",
            "/users/",
            params={"username": username, "password": password},
        )
        return User.model_validate(response.json())

    def test_logged_in(self) -> dict:
        """GET /users/test (requires bearer token)."""
        response = self._http.request("GET", "/users/test")
        return response.json()
