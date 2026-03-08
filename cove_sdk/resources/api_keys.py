from cove_sdk._http import HTTPClient
from cove_sdk.models import APIKeyCreated, APIKeyPublic


class APIKeysClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def create(self, project_id: str) -> APIKeyCreated:
        """POST /api_keys/{project_id} → 201"""
        response = self._http.request("POST", f"/api_keys/{project_id}")
        return APIKeyCreated.model_validate(response.json())

    def list(self) -> list[APIKeyPublic]:
        """GET /api_keys/"""
        response = self._http.request("GET", "/api_keys/")
        return [APIKeyPublic.model_validate(k) for k in response.json()]

    def get(self, key_id: str) -> APIKeyPublic:
        """GET /api_keys/{key_id}"""
        response = self._http.request("GET", f"/api_keys/{key_id}")
        return APIKeyPublic.model_validate(response.json())

    def rotate(self, key_id: str) -> APIKeyCreated:
        """PATCH /api_keys/{key_id}"""
        response = self._http.request("PATCH", f"/api_keys/{key_id}")
        return APIKeyCreated.model_validate(response.json())

    def delete(self, key_id: str) -> None:
        """DELETE /api_keys/{key_id} → 204 (no body)"""
        self._http.request("DELETE", f"/api_keys/{key_id}")
