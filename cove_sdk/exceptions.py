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
