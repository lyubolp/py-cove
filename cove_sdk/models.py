from typing import Any

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: str | None = None
    username: str
    password_hash: str


class Project(BaseModel):
    id: str | None = None
    name: str
    is_public: bool


class APIKeyPublic(BaseModel):
    id: str
    access_for_project_id: str


class APIKeyCreated(BaseModel):
    id: str
    access_for_project_id: str
    key: str


class BaseItem(BaseModel):
    key: str


class KeyValueItem(BaseItem):
    value: str


class JSONItem(BaseItem):
    json_value: dict[str, Any]


class PythonItem(BaseItem):
    python_value: str


class StatusResponse(BaseModel):
    status: str | None = None
    error: str | None = None
    project_id: str | None = None


class ValidationErrorItem(BaseModel):
    loc: list[str | int]
    msg: str
    type: str
    input: Any | None = None
    ctx: dict[str, Any] | None = None


class HTTPValidationError(BaseModel):
    detail: list[ValidationErrorItem]
