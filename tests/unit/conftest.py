"""Shared fixtures for unit tests."""

import pytest
from unittest.mock import MagicMock, patch

from conoha.client import ConoHaClient


@pytest.fixture
def mock_client():
    """Create a ConoHaClient with pre-set token (no real authentication)."""
    with patch.object(ConoHaClient, "authenticate"):
        client = ConoHaClient.__new__(ConoHaClient)
        client.region = "c3j1"
        client.timeout = 30
        client._token = "test-token-12345"
        client._token_expires_at = None
        client._tenant_id = "tenant-id-12345"
        client._user_id = "user-id-12345"
        client._username = "testuser"
        client._password = "testpass"
        client._tenant_name = None
        client._user_endpoints = {}
        client._env_endpoints = {}
        client._catalog_endpoints = {}
        client._identity = None
        client._compute = None
        client._volume = None
        client._image = None
        client._network = None
        client._load_balancer = None
        client._dns = None
        client._object_storage = None
        return client


@pytest.fixture
def mock_response():
    """Factory for creating mock responses."""
    def _make(status_code=200, json_data=None, headers=None, text=""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        resp.headers = headers or {}
        resp.text = text
        resp.content = b""
        return resp
    return _make
