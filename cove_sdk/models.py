from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class ProjectItems(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key_value: list[KeyValueItem] = Field(default_factory=list)
    json_items: list[JSONItem] = Field(default_factory=list, alias="json")
    python: list[PythonItem] = Field(default_factory=list)


class ItemsDeleteResult(BaseModel):
    status: str
    deleted_count: int


class ValidationErrorItem(BaseModel):
    loc: list[str | int]
    msg: str
    type: str
    input: Any | None = None
    ctx: dict[str, Any] | None = None


class HTTPValidationError(BaseModel):
    detail: list[ValidationErrorItem]
