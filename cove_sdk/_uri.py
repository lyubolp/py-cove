from enum import StrEnum
from urllib.parse import urlsplit

from cove_sdk.exceptions import URIParseError


class ResourceType(StrEnum):
    JSON_ITEM = "json_item"
    KEY_VALUE = "key_value"
    PYTHON_ITEM = "python_item"


def parse_uri(uri: str) -> tuple[str, ResourceType, str, str]:
    split_result = urlsplit(uri)

    if split_result.scheme != "cove":
        raise URIParseError(f"Invalid scheme: {split_result.scheme}")

    netloc = split_result.netloc

    path = split_result.path

    try:
        resource, project_id, key = path.strip("/").split("/")
    except ValueError as exc:
        raise URIParseError(f"Invalid path: {path}") from exc

    if resource not in ResourceType.__members__.values():
        raise URIParseError(f"Invalid resource type: {resource}")

    return netloc, ResourceType(resource), project_id, key
