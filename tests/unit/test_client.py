"""Unit tests for the ConoHa client."""

import time
from unittest.mock import patch, MagicMock

import pytest

from conoha.client import ConoHaClient
from conoha.exceptions import AuthenticationError


class TestConoHaClient:
    def test_init_with_token(self):
        """Client can be created with a pre-existing token."""
        client = ConoHaClient(token="pre-existing-token", tenant_id="tid")
        assert client._token == "pre-existing-token"
        assert client.tenant_id == "tid"

    @patch("conoha.client.requests.post")
    def test_authenticate_success(self, mock_post):
        """Successful authentication sets token and tenant."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {"x-subject-token": "new-token-xyz"}
        mock_resp.json.return_value = {
            "token": {
                "project": {"id": "tenant-abc", "name": "test-tenant"},
                "user": {"id": "user-abc", "name": "test-user"},
                "catalog": [],
                "expires_at": "2026-02-18T12:00:00Z",
            }
        }
        mock_post.return_value = mock_resp

        client = ConoHaClient(
            username="testuser",
            password="testpass",
            tenant_id="tenant-abc",
        )
        assert client._token == "new-token-xyz"
        assert client.tenant_id == "tenant-abc"
        assert client.user_id == "user-abc"

    @patch("conoha.client.requests.post")
    def test_authenticate_with_user_id(self, mock_post):
        """Authentication works with user_id instead of username."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {"x-subject-token": "token-by-id"}
        mock_resp.json.return_value = {
            "token": {
                "project": {"id": "tid"},
                "user": {"id": "uid"},
                "catalog": [],
            }
        }
        mock_post.return_value = mock_resp

        client = ConoHaClient(
            user_id="uid",
            password="pass",
            tenant_id="tid",
        )
        assert client._token == "token-by-id"
        # Verify the request body used "id" not "name"
        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        user_block = body["auth"]["identity"]["password"]["user"]
        assert "id" in user_block
        assert "name" not in user_block

    @patch("conoha.client.requests.post")
    def test_authenticate_failure(self, mock_post):
        """Failed authentication raises AuthenticationError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_post.return_value = mock_resp

        with pytest.raises(AuthenticationError):
            ConoHaClient(
                username="bad", password="wrong", tenant_id="tid"
            )

    @patch("conoha.client.requests.post")
    def test_parse_catalog(self, mock_post):
        """Service catalog is parsed into endpoints."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {"x-subject-token": "tok"}
        mock_resp.json.return_value = {
            "token": {
                "project": {"id": "tid"},
                "user": {"id": "uid"},
                "catalog": [
                    {
                        "type": "compute",
                        "endpoints": [
                            {
                                "interface": "public",
                                "url": "https://compute.c3j1.conoha.io",
                            }
                        ],
                    },
                    {
                        "type": "dns",
                        "endpoints": [
                            {
                                "interface": "public",
                                "url": "https://dns-service.c3j1.conoha.io",
                            }
                        ],
                    },
                ],
            }
        }
        mock_post.return_value = mock_resp

        client = ConoHaClient(
            username="u", password="p", tenant_id="t"
        )
        assert client._catalog_endpoints["compute"] == "https://compute.c3j1.conoha.io"
        assert client._catalog_endpoints["dns"] == "https://dns-service.c3j1.conoha.io"

    def test_token_property_no_auth(self):
        """Accessing token without auth raises error."""
        client = ConoHaClient.__new__(ConoHaClient)
        client._token = None
        client._token_expires_at = None
        client._username = None
        client._user_id = None
        client._password = None
        with pytest.raises(AuthenticationError):
            _ = client.token

    def test_token_expired_triggers_reauth(self, mock_client):
        """Expired token triggers re-authentication."""
        mock_client._token_expires_at = time.time() - 100  # expired
        with patch.object(mock_client, "authenticate") as mock_auth:
            mock_auth.side_effect = lambda: setattr(
                mock_client, "_token", "refreshed"
            ) or setattr(mock_client, "_token_expires_at", None)
            token = mock_client.token
            mock_auth.assert_called_once()

    def test_service_properties(self, mock_client):
        """Service properties return correct types."""
        from conoha.identity import IdentityService
        from conoha.compute import ComputeService
        from conoha.volume import VolumeService
        from conoha.image import ImageService
        from conoha.network import NetworkService
        from conoha.loadbalancer import LoadBalancerService
        from conoha.dns import DNSService
        from conoha.object_storage import ObjectStorageService

        assert isinstance(mock_client.identity, IdentityService)
        assert isinstance(mock_client.compute, ComputeService)
        assert isinstance(mock_client.volume, VolumeService)
        assert isinstance(mock_client.image, ImageService)
        assert isinstance(mock_client.network, NetworkService)
        assert isinstance(mock_client.load_balancer, LoadBalancerService)
        assert isinstance(mock_client.dns, DNSService)
        assert isinstance(mock_client.object_storage, ObjectStorageService)

    def test_service_properties_cached(self, mock_client):
        """Service properties return same instance on repeated access."""
        compute1 = mock_client.compute
        compute2 = mock_client.compute
        assert compute1 is compute2

    def test_get_endpoint_fallback(self, mock_client):
        """_get_endpoint falls back to template URL."""
        url = mock_client._get_endpoint("compute")
        assert url == "https://compute.c3j1.conoha.io"

    def test_get_endpoint_from_catalog(self, mock_client):
        """_get_endpoint uses catalog endpoints over template."""
        mock_client._catalog_endpoints["compute"] = "https://catalog.compute.url"
        url = mock_client._get_endpoint("compute")
        assert url == "https://catalog.compute.url"

    def test_get_endpoint_from_env(self, mock_client):
        """_get_endpoint uses env endpoints over catalog."""
        mock_client._catalog_endpoints["compute"] = "https://catalog.compute.url"
        mock_client._env_endpoints["compute"] = "https://env.compute.url"
        url = mock_client._get_endpoint("compute")
        assert url == "https://env.compute.url"

    def test_get_endpoint_from_user(self, mock_client):
        """_get_endpoint uses user-specified endpoints with highest priority."""
        mock_client._catalog_endpoints["compute"] = "https://catalog.compute.url"
        mock_client._env_endpoints["compute"] = "https://env.compute.url"
        mock_client._user_endpoints["compute"] = "https://user.compute.url"
        url = mock_client._get_endpoint("compute")
        assert url == "https://user.compute.url"

    def test_get_endpoint_unknown(self, mock_client):
        """_get_endpoint raises for unknown service."""
        with pytest.raises(ValueError, match="Unknown service"):
            mock_client._get_endpoint("nonexistent")

    def test_init_with_custom_endpoints(self):
        """Client accepts custom endpoints via constructor."""
        client = ConoHaClient(
            token="tok",
            tenant_id="tid",
            endpoints={
                "compute": "https://my-compute.example.com",
                "dns": "https://my-dns.example.com",
            },
        )
        assert client._get_endpoint("compute") == "https://my-compute.example.com"
        assert client._get_endpoint("dns") == "https://my-dns.example.com"
        # Non-overridden service falls back to template
        assert client._get_endpoint("network") == "https://networking.c3j1.conoha.io"

    @patch.dict("os.environ", {"CONOHA_ENDPOINT_COMPUTE": "https://env-compute.example.com"})
    def test_init_loads_env_endpoints(self):
        """Client loads endpoint overrides from environment variables."""
        client = ConoHaClient(token="tok", tenant_id="tid")
        assert client._get_endpoint("compute") == "https://env-compute.example.com"

    @patch.dict("os.environ", {"CONOHA_ENDPOINT_COMPUTE": "https://env-compute.example.com/"})
    def test_env_endpoint_strips_trailing_slash(self):
        """Trailing slash is stripped from env endpoint URLs."""
        client = ConoHaClient(token="tok", tenant_id="tid")
        assert client._get_endpoint("compute") == "https://env-compute.example.com"
