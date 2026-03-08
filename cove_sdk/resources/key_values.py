from cove_sdk._http import HTTPClient
from cove_sdk.models import KeyValueItem, StatusResponse


class KeyValuesClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def list(self, project_id: str) -> list[KeyValueItem]:
        """GET /key_value/{project_id}"""
        response = self._http.request("GET", f"/key_value/{project_id}")
        data = response.json()
        return [KeyValueItem.model_validate(item) for item in data]

    def get(self, project_id: str, key: str) -> KeyValueItem:
        """GET /key_value/{project_id}/{key}"""
        response = self._http.request("GET", f"/key_value/{project_id}/{key}")
        return KeyValueItem.model_validate(response.json())

    def create(self, project_id: str, key: str, value: str) -> StatusResponse:
        """POST /key_value/{project_id}/{key}/{value}"""
        response = self._http.request("POST", f"/key_value/{project_id}/{key}/{value}")
        return StatusResponse.model_validate(response.json())

    def update(
        self,
        project_id: str,
        key: str,
        *,
        value: str | None = None,
        is_public: bool | None = None,
    ) -> StatusResponse:
        """PATCH /key_value/{project_id}/{key}?value=...&is_public=..."""
        params: dict = {}
        if value is not None:
            params["value"] = value
        if is_public is not None:
            params["is_public"] = is_public
        response = self._http.request(
            "PATCH", f"/key_value/{project_id}/{key}", params=params
        )
        return StatusResponse.model_validate(response.json())

    def delete(self, project_id: str, key: str) -> StatusResponse:
        """DELETE /key_value/{project_id}/{key}"""
        response = self._http.request("DELETE", f"/key_value/{project_id}/{key}")
        return StatusResponse.model_validate(response.json())
