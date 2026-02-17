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

    # ── Token Management ──────────────────────────────────────

    def test_validate_token(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"token": {"user": {"id": "uid"}, "expires_at": "2026-02-18T12:00:00Z"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            token_info = svc.validate_token("some-token")
            assert token_info["user"]["id"] == "uid"
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Subject-Token"] == "some-token"

    def test_get_token_info(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"token": {"user": {"id": "uid"}, "catalog": []}},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            info = svc.get_token_info()
            assert info["user"]["id"] == "uid"

    def test_revoke_token(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.revoke_token("old-token")
            assert mock_req.call_args[0][0] == "DELETE"
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Subject-Token"] == "old-token"

    # ── Sub-users ─────────────────────────────────────────────

    def test_list_users(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"users": [{"id": "u1", "name": "sub-user"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            users = svc.list_users()
            assert len(users) == 1
            assert users[0]["name"] == "sub-user"

    def test_create_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            201,
            json_data={"user": {"id": "u2", "name": "new-user"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.create_user("new-user", "password123", email="a@b.com")
            assert user["name"] == "new-user"
            body = mock_req.call_args.kwargs["json"]
            assert body["user"]["name"] == "new-user"
            assert body["user"]["email"] == "a@b.com"

    def test_get_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"user": {"id": "u1", "name": "sub-user"}},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            user = svc.get_user("u1")
            assert user["id"] == "u1"

    def test_update_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"user": {"id": "u1", "name": "renamed"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.update_user("u1", name="renamed")
            assert user["name"] == "renamed"
            assert mock_req.call_args[0][0] == "PATCH"

    def test_delete_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.delete_user("u1")
            assert mock_req.call_args[0][0] == "DELETE"

    # ── Roles ─────────────────────────────────────────────────

    def test_list_roles(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"roles": [{"id": "r1", "name": "admin"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            roles = svc.list_roles()
            assert roles[0]["name"] == "admin"

    def test_list_user_roles(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"roles": [{"id": "r1", "name": "member"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            roles = svc.list_user_roles("pid", "uid")
            assert roles[0]["name"] == "member"
            url = mock_req.call_args[0][1]
            assert "/v3/projects/pid/users/uid/roles" in url

    def test_assign_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.assign_role("pid", "uid", "rid")
            assert mock_req.call_args[0][0] == "PUT"
            url = mock_req.call_args[0][1]
            assert "/v3/projects/pid/users/uid/roles/rid" in url

    def test_unassign_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.unassign_role("pid", "uid", "rid")
            assert mock_req.call_args[0][0] == "DELETE"

    def test_check_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            result = svc.check_role("pid", "uid", "rid")
            assert result is True

    # ── Permissions ───────────────────────────────────────────

    def test_list_permissions(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"permissions": {"compute": True, "dns": False}},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            perms = svc.list_permissions("r1")
            assert perms["compute"] is True

    def test_update_permissions(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"permissions": {"compute": False}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            perms = svc.update_permissions("r1", {"compute": False})
            assert perms["compute"] is False
            body = mock_req.call_args.kwargs["json"]
            assert body["permissions"]["compute"] is False
