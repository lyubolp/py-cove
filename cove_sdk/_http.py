import httpx

from cove_sdk.exceptions import (
    AccessDeniedError,
    AuthenticationError,
    ConflictError,
    CoveAPIError,
    NotFoundError,
    ValidationError,
)
from cove_sdk.models import HTTPValidationError


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
        # 2xx responses are all success — treat 200, 201, 204 etc. as OK
        if response.status_code < 400:
            return

        status = response.status_code

        # Try to extract a detail message from the response body
        try:
            body = response.json()
            detail = (
                body.get("detail", response.text)
                if isinstance(body, dict)
                else response.text
            )
        except Exception:
            detail = response.text

        if status == 400:
            raise ConflictError(status, detail)
        elif status == 401:
            raise AuthenticationError(status, detail)
        elif status == 403:
            raise AccessDeniedError(status, detail)
        elif status == 404:
            raise NotFoundError(status, detail)
        elif status == 422:
            errors: list = []
            try:
                validation_error = HTTPValidationError.model_validate(response.json())
                errors = validation_error.detail
                detail = str(detail)
            except Exception:
                pass
            raise ValidationError(status, detail, errors)
        else:
            raise CoveAPIError(status, detail)

    def close(self) -> None:
        self._client.close()
