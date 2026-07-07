# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`py-cove` is a Python SDK wrapping the [Cove](https://github.com/lyubolp/cove) REST API — a service for storing key-value, JSON, and Python-code items scoped to projects, with JWT and API-key auth. The SDK targets Python 3.12+ and uses `httpx` (sync client) + `pydantic` for models.

## Commands

The project is managed with `uv` (`uv.lock` is checked in) and built with `hatchling`.

```bash
uv sync              # install/sync dependencies into .venv
uv run python main.py
uv build              # produces dist/*.whl and dist/*.tar.gz
```

There is currently no test suite and no configured linter/type-checker in `pyproject.toml` — don't assume `pytest`/`ruff`/`mypy` commands exist unless you add the tooling yourself.

## Architecture

The SDK follows a hub-and-spoke design: `CoveClient` (`cove_sdk/client.py`) owns a single shared `HTTPClient` (`cove_sdk/_http.py`) and hands it to one resource client per API area. All request/response logic for a resource lives in its own file under `cove_sdk/resources/`; there is no cross-resource coupling except through the shared `HTTPClient`.

- **`_http.py`** — the only place that talks to `httpx` directly. `HTTPClient.request()` injects `Authorization: Bearer {token}` and/or `x-api-key` headers (both can be set at once — the server checks JWT first, then falls back to the API key), then maps non-2xx responses to exceptions via `_raise_for_status`. All 2xx codes (200/201/204) are treated as success.
- **`request(..., raise_for_404=True)`** — resource `get()` methods that need "return `None` instead of raising" behavior (used by `fetch_uri`, see below) pass `raise_for_404=False` and check `response.status_code == 404` themselves rather than letting `_raise_for_status` raise `NotFoundError`. `projects.get`, `projects.get_items`, `key_values.get`, `json_items.get`, and `python_items.get` all follow this pattern and return `Optional[Model]`.
- **Exception mapping** (`exceptions.py`): 400→`ConflictError`, 401→`AuthenticationError`, 403→`AccessDeniedError`, 404→`NotFoundError`, 422→`ValidationError` (parses the body into `HTTPValidationError` and attaches `.errors`), anything else→`CoveAPIError`. All inherit from `CoveAPIError`.
- **Models** (`models.py`): plain `pydantic.BaseModel`s. `BaseItem` (has `key: str`) is the common parent of `KeyValueItem`, `JSONItem`, and `PythonItem` — each adds one payload field (`value`, `json_value`, `python_value` respectively). `StatusResponse` is a best-effort shape for the many endpoints that return an untyped `dict[str, str]`.
- **Item resource clients** (`json_items.py`, `key_values.py`, `python_items.py`) share the same CRUD shape (`list`/`get`/`create`/`update`/`delete`) but differ in wire format: `key_values.create` puts the value in the URL path, `json_items` sends `{"value": ...}` as a JSON body, and `python_items` sends raw code as `content=` with `Content-Type: text/plain`.
- **Cross-type item ops** (`resources/projects.py`): `projects.get_items(project_id)` and `projects.delete_items(project_id)` hit `/project/{project_id}/items`, operating on key-value, JSON, and Python items together as a group rather than through the per-type resource clients. `get_items` returns `ProjectItems`, whose `json` field is exposed as `.json_items` (aliased via `Field(alias="json")` in `models.py` since `json` shadows `BaseModel`'s legacy `.json()` method) — construct/parse it with `populate_by_name=True` in mind if you touch that model. `delete_items` returns `ItemsDeleteResult` (`status` + `deleted_count`), not the general-purpose `StatusResponse`.
- **URI handling** (`_uri.py` + `fetch_uri` in `client.py`): Cove resources can be addressed as `cove://<host>/<resource>/<project_id>/<key>` where `<resource>` is one of the `ResourceType` enum values (`json_item`, `key_value`, `python_item`). `parse_uri` validates and unpacks the URI; `build_uri(host, resource, project_id, key)` is the inverse (round-trips with `parse_uri`); `fetch_uri(uri, api_key)` opens a short-lived `CoveClient` scoped to that host/api_key, dispatches on `ResourceType`, and returns a `BaseItem | None`. `is_cove_uri` is a cheap scheme check for callers deciding whether a string should be treated as a Cove URI at all.
- **`__init__.py`** re-exports the full public surface (client, models, exceptions, `fetch_uri`, `build_uri`, `is_cove_uri`, `ResourceType`) — when adding a new model, exception, or `_uri.py` helper, add it here too or it won't be part of the package's public API.

`instructions.md` is the original design spec for the SDK; the shipped code has since diverged from it (e.g. it predates `json_items`/`python_items`/`BaseItem`, the 404→`None` convention, and the URI helpers), so treat the actual source under `cove_sdk/` as the source of truth over that document.
