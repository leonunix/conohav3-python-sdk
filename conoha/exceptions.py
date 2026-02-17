"""ConoHa SDK custom exceptions."""


class ConoHaError(Exception):
    """Base exception for ConoHa SDK."""


class AuthenticationError(ConoHaError):
    """Authentication failed."""


class TokenExpiredError(AuthenticationError):
    """Token has expired."""


class APIError(ConoHaError):
    """API request failed."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(APIError):
    """Resource not found (404)."""


class ConflictError(APIError):
    """Resource conflict (409)."""


class BadRequestError(APIError):
    """Bad request (400)."""


class ForbiddenError(APIError):
    """Forbidden (403)."""
