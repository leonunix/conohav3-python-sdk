"""Unit tests for Identity API service."""

from unittest.mock import patch, MagicMock

import pytest

from conoha.identity import IdentityService


class TestIdentityService:
    def test_list_credentials(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "credentials": [
                    {"access": "key1", "secret": "sec1", "user_id": "uid"}
                ]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            creds = svc.list_credentials("uid")
            assert len(creds) == 1
            assert creds[0]["access"] == "key1"

    def test_create_credential(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "credential": {
                    "access": "new-key",
                    "secret": "new-secret",
                    "user_id": "uid",
                    "tenant_id": "tid",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            cred = svc.create_credential("uid", "tid")
            assert cred["access"] == "new-key"
            assert cred["tenant_id"] == "tid"

    def test_get_credential(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "credential": {
                    "access": "key1",
                    "secret": "sec1",
                    "user_id": "uid",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            cred = svc.get_credential("uid", "key1")
            assert cred["secret"] == "sec1"

    def test_delete_credential(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_credential("uid", "key1")  # Should not raise
