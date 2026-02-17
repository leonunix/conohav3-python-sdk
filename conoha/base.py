"""Base service class for ConoHa API services."""

import requests

from .exceptions import (
    APIError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    TokenExpiredError,
)


class BaseService:
    """Base class for all ConoHa API service modules."""

    def __init__(self, client):
        self._client = client

    @property
    def _token(self):
        return self._client.token

    @property
    def _tenant_id(self):
        return self._client.tenant_id

    def _get_headers(self, extra_headers=None):
        headers = {
            "Accept": "application/json",
            "X-Auth-Token": self._token,
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _request(self, method, url, **kwargs):
        headers = self._get_headers(kwargs.pop("extra_headers", None))
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        timeout = kwargs.pop("timeout", self._client.timeout)

        response = requests.request(
            method, url, headers=headers, timeout=timeout, **kwargs
        )
        self._handle_response(response)
        return response

    def _handle_response(self, response):
        if response.status_code >= 400:
            message = f"HTTP {response.status_code}"
            try:
                body = response.json()
                if "error" in body:
                    message = body["error"].get("message", message)
                elif "message" in body:
                    message = body["message"]
            except (ValueError, KeyError):
                message = response.text or message

            error_map = {
                400: BadRequestError,
                401: TokenExpiredError,
                403: ForbiddenError,
                404: NotFoundError,
                409: ConflictError,
            }
            error_class = error_map.get(response.status_code, APIError)
            raise error_class(message, response.status_code, response)

    def _get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def _post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)

    def _put(self, url, **kwargs):
        return self._request("PUT", url, **kwargs)

    def _patch(self, url, **kwargs):
        return self._request("PATCH", url, **kwargs)

    def _delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)

    def _head(self, url, **kwargs):
        return self._request("HEAD", url, **kwargs)
