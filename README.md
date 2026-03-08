# py-cove

A Python SDK for the [Cove](https://github.com/lyubolp/cove) REST API. It provides a clean, typed interface for managing users, projects, key-value pairs, and API keys.

---

## Requirements

- Python 3.12+
- [`httpx`](https://www.python-httpx.org/)
- [`pydantic`](https://docs.pydantic.dev/)

---

## Installation

Install directly from source:

```bash
pip install .
```

Or add as a dependency in your own project using the package name `py-cove`.

---

## Authentication

Two authentication mechanisms are supported and can be used simultaneously:

| Mechanism | How it works |
|---|---|
| **JWT Bearer Token** | Obtained by calling `client.login()`. Sent as `Authorization: Bearer {token}`. |
| **API Key** | Scoped to a single project. Sent as the `x-api-key` header. |

Pass credentials at construction time, or call `login()` at any point to acquire and store a JWT automatically.

---

## Quick Start

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000") as client:
    client.login("alice", "s3cret")

    # Check server health
    print(client.health())  # {'message': 'healthy'}
```

---

## Usage Examples

### User management

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000") as client:
    # Create a new user
    user = client.users.create("bob", "password123")
    print(user.username)  # "bob"

    # Log in and store the JWT on the client automatically
    client.login("bob", "password123")

    # Verify the token works
    result = client.users.test_logged_in()
    print(result)
```

### Projects

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000") as client:
    client.login("alice", "s3cret")

    # Create a project
    resp = client.projects.create("my-config")
    project_id = resp.project_id

    # List all projects accessible to the current user
    for project in client.projects.list():
        print(project.id, project.name, project.is_public)

    # Rename a project and make it public
    client.projects.update(project_id, name="my-config-v2", is_public=True)

    # Grant another user access
    client.projects.add_user(project_id, other_user_id)

    # Delete the project
    client.projects.delete(project_id)
```

### Key-value pairs

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000") as client:
    client.login("alice", "s3cret")

    project_id = "..."

    # Store a value
    client.key_values.create(project_id, "database_url", "postgres://localhost/mydb")

    # Read a single value
    item = client.key_values.get(project_id, "database_url")
    print(item.value)  # "postgres://localhost/mydb"

    # Update a value
    client.key_values.update(project_id, "database_url", value="postgres://prod-host/mydb")

    # List all key-value pairs in a project
    for kv in client.key_values.list(project_id):
        print(f"{kv.key}={kv.value}")

    # Delete a key
    client.key_values.delete(project_id, "database_url")
```

### API key authentication

Use an API key instead of (or alongside) a JWT. API keys are scoped to a single project.

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000", api_key="cove_abc123...") as client:
    items = client.key_values.list("some-project-id")
    for kv in items:
        print(f"{kv.key}={kv.value}")
```

### Managing API keys

```python
from cove_sdk import CoveClient

with CoveClient(base_url="http://localhost:8000") as client:
    client.login("alice", "s3cret")

    project_id = "..."

    # Create a new API key for a project
    created = client.api_keys.create(project_id)
    print(created.key)   # store this — it won't be shown again

    # List all API keys owned by the current user
    for key in client.api_keys.list():
        print(key.id, key.access_for_project_id)

    # Rotate (regenerate) an API key
    rotated = client.api_keys.rotate(created.id)
    print(rotated.key)   # new key value

    # Delete an API key
    client.api_keys.delete(created.id)
```

### Error handling

```python
from cove_sdk import (
    CoveClient,
    AuthenticationError,
    AccessDeniedError,
    NotFoundError,
    ConflictError,
    ValidationError,
    CoveAPIError,
)

with CoveClient(base_url="http://localhost:8000") as client:
    try:
        client.login("alice", "wrong-password")
    except AuthenticationError as e:
        print(f"Login failed ({e.status_code}): {e.detail}")

    try:
        client.projects.get("nonexistent-id")
    except NotFoundError as e:
        print(f"Not found: {e.detail}")

    try:
        client.users.create("alice", "pass")  # duplicate username
    except ConflictError as e:
        print(f"Conflict: {e.detail}")

    try:
        client.projects.list()
    except ValidationError as e:
        print(f"Validation failed: {e.errors}")

    # Catch-all for unexpected errors
    except CoveAPIError as e:
        print(f"API error {e.status_code}: {e.detail}")
```

---

## Exception Reference

| Exception | HTTP Status | Meaning |
|---|---|---|
| `AuthenticationError` | 401 | Missing, invalid, or expired JWT |
| `AccessDeniedError` | 403 | User lacks project access |
| `NotFoundError` | 404 | Resource does not exist |
| `ConflictError` | 400 | Duplicate resource (e.g. username already taken) |
| `ValidationError` | 422 | Request validation failure — `.errors` contains details |
| `CoveAPIError` | any other 4xx/5xx | Base class for all SDK errors |

---

## Package Layout

```
cove_sdk/
├── __init__.py            # Re-exports: CoveClient, all models, all exceptions
├── client.py              # CoveClient (top-level orchestrator)
├── models.py              # Pydantic models
├── exceptions.py          # Exception hierarchy
├── _http.py               # HTTP wrapper (auth headers, status → exception mapping)
└── resources/
    ├── users.py           # UsersClient
    ├── projects.py        # ProjectsClient
    ├── key_values.py      # KeyValuesClient
    └── api_keys.py        # APIKeysClient
```
