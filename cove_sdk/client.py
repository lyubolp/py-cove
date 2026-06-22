from cove_sdk._http import HTTPClient
from cove_sdk._uri import ResourceType, parse_uri
from cove_sdk.models import BaseItem, JSONItem, KeyValueItem, PythonItem, Token
from cove_sdk.resources.api_keys import APIKeysClient
from cove_sdk.resources.json_items import JSONItemsClient
from cove_sdk.resources.key_values import KeyValuesClient
from cove_sdk.resources.projects import ProjectsClient
from cove_sdk.resources.python_items import PythonItemsClient
from cove_sdk.resources.users import UsersClient


class CoveClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self._http = HTTPClient(base_url=base_url, timeout=timeout)
        if token:
            self._http.token = token
        if api_key:
            self._http.api_key = api_key

        self.users = UsersClient(self._http)
        self.projects = ProjectsClient(self._http)
        self.key_values = KeyValuesClient(self._http)
        self.json_items = JSONItemsClient(self._http)
        self.python_items = PythonItemsClient(self._http)
        self.api_keys = APIKeysClient(self._http)

    def login(self, username: str, password: str) -> Token:
        """Convenience: calls users.login(), stores token on the client."""
        token = self.users.login(username, password)
        self._http.token = token.access_token
        return token

    def health(self) -> dict:
        """GET /health — no auth required."""
        response = self._http.request("GET", "/health")
        return response.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fetch_uri(uri: str, api_key: str) -> BaseItem | None:
    """Fetch a resource by its URI. The URI format is: cove://{host}/{resource_type}/{project_id}/{key}"""

    host, resource, project_id, key = parse_uri(uri)

    with CoveClient(base_url=f"http://{host}", api_key=api_key) as client:
        match resource:
            case ResourceType.JSON_ITEM:
                return client.json_items.get(project_id, key)
            case ResourceType.KEY_VALUE:
                return client.key_values.get(project_id, key)
            case ResourceType.PYTHON_ITEM:
                return client.python_items.get(project_id, key)
