from cove_sdk._http import HTTPClient
from cove_sdk.models import PythonItem, StatusResponse


class PythonItemsClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def list(self, project_id: str) -> list[PythonItem]:
        """GET /python_item/{project_id}"""
        response = self._http.request("GET", f"/python_item/{project_id}")
        data = response.json()
        return [PythonItem.model_validate(item) for item in data]

    def get(self, project_id: str, key: str) -> PythonItem:
        """GET /python_item/{project_id}/{key}"""
        response = self._http.request("GET", f"/python_item/{project_id}/{key}")
        return PythonItem.model_validate(response.json())

    def create(self, project_id: str, key: str, code: str) -> StatusResponse:
        """POST /python_item/{project_id}/{key}"""
        response = self._http.request(
            "POST",
            f"/python_item/{project_id}/{key}",
            content=code,
            headers={"Content-Type": "text/plain"},
        )
        return StatusResponse.model_validate(response.json())

    def update(self, project_id: str, key: str, code: str) -> StatusResponse:
        """PATCH /python_item/{project_id}/{key}"""
        response = self._http.request(
            "PATCH",
            f"/python_item/{project_id}/{key}",
            content=code,
            headers={"Content-Type": "text/plain"},
        )
        return StatusResponse.model_validate(response.json())

    def delete(self, project_id: str, key: str) -> StatusResponse:
        """DELETE /python_item/{project_id}/{key}"""
        response = self._http.request("DELETE", f"/python_item/{project_id}/{key}")
        return StatusResponse.model_validate(response.json())
