# Cove Python SDK — Implementation Specification

This document describes the complete design for a Python SDK that wraps the Cove REST API. It is intended as a self-contained reference for implementation.

---

## Base URL & Authentication

The SDK communicates with a Cove server over HTTP. Two authentication mechanisms are supported and can be used simultaneously:

1. **JWT Bearer Token** — sent as `Authorization: Bearer {token}`. Obtained by calling `POST /users/token` with username/password.
2. **API Key** — sent as the `x-api-key` header. Scoped to a single project.

The server checks JWT first, then falls back to the API key.

---

## File Layout

```
cove_sdk/
├── __init__.py            # Re-exports: CoveClient, all models, all exceptions
├── client.py              # CoveClient (top-level orchestrator)
├── models.py              # Pydantic models
├── exceptions.py          # Exception hierarchy
├── _http.py               # Thin HTTP wrapper (handles headers, status→exception mapping)
└── resources/
    ├── __init__.py
    ├── users.py           # UsersClient
    ├── projects.py        # ProjectsClient
    ├── key_values.py      # KeyValuesClient
    └── api_keys.py        # APIKeysClient
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `httpx` | HTTP client (sync) |
| `pydantic` | Model validation / serialization |

The SDK should target **Python 3.12+** to match the server.

---

## Models (`models.py`)

All models are `pydantic.BaseModel` subclasses.

### `Token`

```python
class Token(BaseModel):
    access_token: str
    token_type: str
```

### `User`

```python
class User(BaseModel):
    id: str | None = None
    username: str
    password_hash: str
```

### `Project`

```python
class Project(BaseModel):
    id: str | None = None
    name: str
    is_public: bool
```

### `APIKeyPublic`

```python
class APIKeyPublic(BaseModel):
    id: str
    access_for_project_id: str
```

### `APIKeyCreated`

```python
class APIKeyCreated(BaseModel):
    id: str
    access_for_project_id: str
    key: str
```

### `KeyValueItem`

> Not in the OpenAPI schemas (endpoints return untyped JSON), but useful for SDK consumers.

```python
class KeyValueItem(BaseModel):
    key: str
    value: str
```

### `StatusResponse`

> Many mutating endpoints return `dict[str, str]`. This model captures the common shape.

```python
class StatusResponse(BaseModel):
    status: str | None = None
    error: str | None = None
    project_id: str | None = None
```

### `ValidationErrorItem`

```python
from typing import Any

class ValidationErrorItem(BaseModel):
    loc: list[str | int]
    msg: str
    type: str
    input: Any | None = None
    ctx: dict[str, Any] | None = None
```

### `HTTPValidationError`

```python
class HTTPValidationError(BaseModel):
    detail: list[ValidationErrorItem]
```

---

## Exceptions (`exceptions.py`)

```python
class CoveAPIError(Exception):
    """Base class for all SDK errors."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class AuthenticationError(CoveAPIError):
    """401 — missing, invalid, or expired JWT."""
    pass


class AccessDeniedError(CoveAPIError):
    """403 — user lacks project access."""
    pass


class NotFoundError(CoveAPIError):
    """404 — resource does not exist."""
    pass


class ConflictError(CoveAPIError):
    """400 — duplicate resource (e.g. username)."""
    pass


class ValidationError(CoveAPIError):
    """422 — request validation failure."""
    def __init__(self, status_code: int, detail: str, errors: list):
        super().__init__(status_code, detail)
        self.errors = errors  # list[ValidationErrorItem]
```

### Status code → exception mapping

| HTTP Status | Exception |
|---|---|
| 400 | `ConflictError` |
| 401 | `AuthenticationError` |
| 403 | `AccessDeniedError` |
| 404 | `NotFoundError` |
| 422 | `ValidationError` (parse body into `HTTPValidationError`, attach `.errors`) |
| Any other 4xx/5xx | `CoveAPIError` |

This mapping should be implemented in `_http.py` and applied after every request.

---

## HTTP Layer (`_http.py`)

A thin wrapper around `httpx.Client`.

### Responsibilities

1. **Base URL handling** — all paths are relative to the configured `base_url`.
2. **Auth headers** — injects `Authorization` and/or `x-api-key` on every request.
3. **Status → exception mapping** — calls `response.raise_for_status()`-equivalent logic using the table above.
4. **Timeout** — configurable, default 30 seconds.

### Suggested interface

```python
class HTTPClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self._client = httpx.Client(base_url=base_url, timeout=timeout)
        self.token: str | None = None
        self.api_key: str | None = None

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.api_key:
            headers["x-api-key"] = self.api_key
        response = self._client.request(method, path, headers=headers, **kwargs)
        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: httpx.Response) -> None:
        # Implement the mapping table here
        ...

    def close(self) -> None:
        self._client.close()
```

---

## Top-Level Client (`client.py`)

### `CoveClient`

```python
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
```

---

## Resource Clients (`resources/`)

Each resource client receives the shared `HTTPClient` instance in its constructor.

### `UsersClient` (`resources/users.py`)

```python
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
```

### `ProjectsClient` (`resources/projects.py`)

```python
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
        response = self._http.request("DELETE", f"/project/{project_id}/access/{user_id}")
        return StatusResponse.model_validate(response.json())
```

### `KeyValuesClient` (`resources/key_values.py`)

```python
class KeyValuesClient:
    def __init__(self, http: HTTPClient):
        self._http = http

    def list(self, project_id: str) -> list[KeyValueItem]:
        """GET /key_value/{project_id}"""
        response = self._http.request("GET", f"/key_value/{project_id}")
        data = response.json()
        # The server returns a list of objects with "key" and "value" fields
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
        response = self._http.request("PATCH", f"/key_value/{project_id}/{key}", params=params)
        return StatusResponse.model_validate(response.json())

    def delete(self, project_id: str, key: str) -> StatusResponse:
        """DELETE /key_value/{project_id}/{key}"""
        response = self._http.request("DELETE", f"/key_value/{project_id}/{key}")
        return StatusResponse.model_validate(response.json())
```

### `APIKeysClient` (`resources/api_keys.py`)

```python
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
```

---

## `__init__.py` Re-exports

```python
# filepath: cove_sdk/__init__.py
from cove_sdk.client import CoveClient
from cove_sdk.models import (
    Token,
    User,
    Project,
    APIKeyPublic,
    APIKeyCreated,
    KeyValueItem,
    StatusResponse,
    ValidationErrorItem,
    HTTPValidationError,
)
from cove_sdk.exceptions import (
    CoveAPIError,
    AuthenticationError,
    AccessDeniedError,
    NotFoundError,
    ConflictError,
    ValidationError,
)

__all__ = [
    "CoveClient",
    "Token",
    "User",
    "Project",
    "APIKeyPublic",
    "APIKeyCreated",
    "KeyValueItem",
    "StatusResponse",
    "ValidationErrorItem",
    "HTTPValidationError",
    "CoveAPIError",
    "AuthenticationError",
    "AccessDeniedError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
]
```

---

## Usage Examples

### Basic login + CRUD

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000") as client:
    # Authenticate
    client.login("alice", "s3cret")

    # Create a project
    result = client.projects.create("my-config")
    project_id = result.project_id

    # Add a key-value pair
    client.key_values.create(project_id, "database_url", "postgres://localhost/mydb")

    # Read it back
    item = client.key_values.get(project_id, "database_url")
    print(item.value)  # "postgres://localhost/mydb"

    # List all items
    items = client.key_values.list(project_id)
    for kv in items:
        print(f"{kv.key}={kv.value}")
```

### API key authentication

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000", api_key="cove_abc123...") as client:
    items = client.key_values.list("some-project-id")
```

### Error handling

```python
from cove_sdk import CoveClient, AuthenticationError, NotFoundError

with CoveClient(base_url="http://localhost:8000") as client:
    try:
        client.login("alice", "wrong-password")
    except AuthenticationError as e:
        print(f"Login failed: {e.detail}")

    try:
        client.projects.get("nonexistent-id")
    except NotFoundError as e:
        print(f"Project not found: {e.detail}")
```

---

## Important Implementation Notes

1. **`POST /users/token`** uses `application/x-www-form-urlencoded` content type (not JSON). Use `data=` not `json=` in the httpx call.

2. **`POST /api_keys/{project_id}`** returns HTTP **201** on success (not 200). The `_raise_for_status` logic must treat 201 and 204 as success.

3. **`DELETE /api_keys/{key_id}`** returns HTTP **204** with no body. The `delete` method should return `None`.

4. **Query parameters** — `update` methods on Projects and KeyValues pass optional fields as query parameters (not request body). Only include parameters that are not `None`.

5. **`KeyValue.value`** is always a `str` — the SDK should not attempt numeric coercion.

6. **The `StatusResponse` model** is a best-effort parse of various `dict[str, str]` responses. Use `model_validate` with lenient settings or just parse the JSON dict.

7. **Context manager support** — `CoveClient` should support `with` statements to ensure the underlying `httpx.Client` is closed.

8. **The server's OpenAPI spec** is available at `/openapi.json` and Swagger UI at `/docs` — but the SDK should not depend on these at runtime.

---

## OpenAPI Endpoint Reference Table

| Method | Path | Auth | Request | Success Response |
|---|---|---|---|---|
| `GET` | `/health` | None | — | `200 {}` |
| `POST` | `/users/token` | None | Form: `username`, `password`, `grant_type` | `200 Token` |
| `POST` | `/users/` | None | Query: `username`, `password` | `200 User` |
| `GET` | `/users/test` | JWT | — | `200 {}` |
| `GET` | `/project/` | JWT or API key | — | `200 list[Project]` |
| `GET` | `/project/{project_id}` | JWT or API key | — | `200 Project` |
| `POST` | `/project/{name}` | JWT | — | `200 dict` |
| `PATCH` | `/project/{project_id}` | JWT | Query: `name?`, `is_public?` | `200 dict` |
| `DELETE` | `/project/{project_id}` | JWT | — | `200 dict` |
| `POST` | `/project/{project_id}/access/{user_id}` | JWT | — | `200 dict` |
| `DELETE` | `/project/{project_id}/access/{user_id}` | JWT | — | `200 dict` |
| `GET` | `/key_value/{project_id}` | JWT or API key | — | `200 list` |
| `GET` | `/key_value/{project_id}/{key}` | JWT or API key | — | `200 object` |
| `POST` | `/key_value/{project_id}/{key}/{value}` | JWT or API key | — | `200 dict` |
| `PATCH` | `/key_value/{project_id}/{key}` | JWT or API key | Query: `value?`, `is_public?` | `200 dict` |
| `DELETE` | `/key_value/{project_id}/{key}` | JWT or API key | — | `200 dict` |
| `POST` | `/api_keys/{project_id}` | JWT | — | `201 APIKeyCreated` |
| `GET` | `/api_keys/` | JWT | — | `200 list[APIKeyPublic]` |
| `GET` | `/api_keys/{key_id}` | JWT | — | `200 APIKeyPublic` |
| `PATCH` | `/api_keys/{key_id}` | JWT | — | `200 APIKeyCreated` |
| `DELETE` | `/api_keys/{key_id}` | JWT | — | `204 (no body)` |