"""Unit tests for base service class and error handling."""

from unittest.mock import patch, MagicMock

import pytest

from conoha.base import BaseService
from conoha.exceptions import (
    APIError,
    BadRequestError,
    NotFoundError,
    ForbiddenError,
    TokenExpiredError,
    ConflictError,
)


class TestBaseService:
    def test_get_headers(self, mock_client):
        svc = BaseService(mock_client)
        headers = svc._get_headers()
        assert headers["X-Auth-Token"] == "test-token-12345"
        assert headers["Accept"] == "application/json"

    def test_get_headers_with_extra(self, mock_client):
        svc = BaseService(mock_client)
        headers = svc._get_headers({"Content-Type": "application/octet-stream"})
        assert headers["Content-Type"] == "application/octet-stream"
        assert "X-Auth-Token" in headers

    def test_handle_400(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(400, text="Bad Request")
        with pytest.raises(BadRequestError) as exc_info:
            svc._handle_response(resp)
        assert exc_info.value.status_code == 400

    def test_handle_401(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(401, text="Unauthorized")
        with pytest.raises(TokenExpiredError):
            svc._handle_response(resp)

    def test_handle_403(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(403, text="Forbidden")
        with pytest.raises(ForbiddenError):
            svc._handle_response(resp)

    def test_handle_404(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(404, text="Not Found")
        with pytest.raises(NotFoundError):
            svc._handle_response(resp)

    def test_handle_409(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(409, text="Conflict")
        with pytest.raises(ConflictError):
            svc._handle_response(resp)

    def test_handle_500(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(500, text="Internal Server Error")
        with pytest.raises(APIError) as exc_info:
            svc._handle_response(resp)
        assert exc_info.value.status_code == 500

    def test_handle_error_with_json_body(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(
            400, json_data={"error": {"message": "Invalid parameter"}}
        )
        with pytest.raises(BadRequestError, match="Invalid parameter"):
            svc._handle_response(resp)

    def test_handle_success(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(200)
        svc._handle_response(resp)  # Should not raise

    def test_handle_204(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(204)
        svc._handle_response(resp)  # Should not raise

    def test_request_methods(self, mock_client, mock_response):
        svc = BaseService(mock_client)
        resp = mock_response(200, json_data={"ok": True})
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc._get("https://example.com/test")
            assert mock_req.call_args[0][0] == "GET"

            svc._post("https://example.com/test", json={"a": 1})
            assert mock_req.call_args[0][0] == "POST"

            svc._put("https://example.com/test")
            assert mock_req.call_args[0][0] == "PUT"

            svc._delete("https://example.com/test")
            assert mock_req.call_args[0][0] == "DELETE"

            svc._head("https://example.com/test")
            assert mock_req.call_args[0][0] == "HEAD"

            svc._patch("https://example.com/test")
            assert mock_req.call_args[0][0] == "PATCH"
