from cove_sdk._http import HTTPClient
from cove_sdk.models import Project, StatusResponse


class ProjectsClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def list(self) -> list[Project]:
        """GET /project/"""
        response = self._http.request("GET", "/project/")
        return [Project.model_validate(p) for p in response.json()]

    def get(self, project_id: str) -> Project:
        """GET /project/{project_id}"""
        response = self._http.request("GET", f"/project/{project_id}")
        return Project.model_validate(response.json())

    def create(self, name: str) -> StatusResponse:
        """POST /project/{name}"""
        response = self._http.request("POST", f"/project/{name}")
        return StatusResponse.model_validate(response.json())

    def update(
        self,
        project_id: str,
        *,
        name: str | None = None,
        is_public: bool | None = None,
    ) -> StatusResponse:
        """PATCH /project/{project_id}?name=...&is_public=..."""
        params: dict = {}
        if name is not None:
            params["name"] = name
        if is_public is not None:
            params["is_public"] = is_public
        response = self._http.request("PATCH", f"/project/{project_id}", params=params)
        return StatusResponse.model_validate(response.json())

    def delete(self, project_id: str) -> StatusResponse:
        """DELETE /project/{project_id}"""
        response = self._http.request("DELETE", f"/project/{project_id}")
        return StatusResponse.model_validate(response.json())

    def add_user(self, project_id: str, user_id: str) -> StatusResponse:
        """POST /project/{project_id}/access/{user_id}"""
        response = self._http.request("POST", f"/project/{project_id}/access/{user_id}")
        return StatusResponse.model_validate(response.json())

    def remove_user(self, project_id: str, user_id: str) -> StatusResponse:
        """DELETE /project/{project_id}/access/{user_id}"""
        response = self._http.request(
            "DELETE", f"/project/{project_id}/access/{user_id}"
        )
        return StatusResponse.model_validate(response.json())
