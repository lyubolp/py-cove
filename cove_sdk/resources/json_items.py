from typing import Any

from cove_sdk._http import HTTPClient
from cove_sdk.models import JSONItem, StatusResponse


class JSONItemsClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def list(self, project_id: str) -> list[JSONItem]:
        """GET /json_item/{project_id}"""
        response = self._http.request("GET", f"/json_item/{project_id}")
        data = response.json()
        return [JSONItem.model_validate(item) for item in data]

    def get(self, project_id: str, key: str) -> JSONItem:
        """GET /json_item/{project_id}/{key}"""
        response = self._http.request("GET", f"/json_item/{project_id}/{key}")
        return JSONItem.model_validate(response.json())

    def create(self, project_id: str, key: str, value: dict[str, Any]) -> StatusResponse:
        """POST /json_item/{project_id}/{key}"""
        response = self._http.request(
            "POST", f"/json_item/{project_id}/{key}", json={"value": value}
        )
        return StatusResponse.model_validate(response.json())

    def update(self, project_id: str, key: str, value: dict[str, Any]) -> StatusResponse:
        """PATCH /json_item/{project_id}/{key}"""
        response = self._http.request(
            "PATCH", f"/json_item/{project_id}/{key}", json={"value": value}
        )
        return StatusResponse.model_validate(response.json())

    def delete(self, project_id: str, key: str) -> StatusResponse:
        """DELETE /json_item/{project_id}/{key}"""
        response = self._http.request("DELETE", f"/json_item/{project_id}/{key}")
        return StatusResponse.model_validate(response.json())
