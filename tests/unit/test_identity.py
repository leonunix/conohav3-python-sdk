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

    # ── Sub-users ─────────────────────────────────────────────

    def test_list_users(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"users": [{"id": "u1", "name": "sub-user"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            users = svc.list_users()
            assert len(users) == 1
            assert users[0]["name"] == "sub-user"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users" in url

    def test_create_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "user": {"id": "u2", "name": "sub-user-u2",
                         "roles": [{"id": "r1", "name": "myrole"}]}
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.create_user("Passw0rd!", ["r1"])
            assert user["id"] == "u2"
            body = mock_req.call_args.kwargs["json"]
            assert body["user"]["password"] == "Passw0rd!"
            assert body["user"]["roles"] == ["r1"]
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users" in url

    def test_get_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"user": {"id": "u1", "name": "sub-user"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.get_user("u1")
            assert user["id"] == "u1"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/u1" in url

    def test_update_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"user": {"id": "u1", "name": "sub-user"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.update_user("u1", "NewPassw0rd!")
            assert user["id"] == "u1"
            assert mock_req.call_args[0][0] == "PUT"
            body = mock_req.call_args.kwargs["json"]
            assert body["user"]["password"] == "NewPassw0rd!"

    def test_delete_user(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.delete_user("u1")
            assert mock_req.call_args[0][0] == "DELETE"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/u1" in url

    def test_assign_roles(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"user": {"id": "u1", "name": "sub",
                                "roles": [{"id": "r1", "name": "role1"}]}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.assign_roles("u1", ["r1"])
            assert user["roles"][0]["id"] == "r1"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/u1/assign" in url
            body = mock_req.call_args.kwargs["json"]
            assert body["roles"] == ["r1"]

    def test_unassign_roles(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"user": {"id": "u1", "name": "sub", "roles": []}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            user = svc.unassign_roles("u1", ["r1"])
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/u1/unassign" in url
            body = mock_req.call_args.kwargs["json"]
            assert body["roles"] == ["r1"]

    # ── Roles ─────────────────────────────────────────────────

    def test_list_roles(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"roles": [{"id": "r1", "name": "admin", "visibility": "private"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            roles = svc.list_roles()
            assert roles[0]["name"] == "admin"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles" in url

    def test_create_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"role": {"id": "r2", "name": "viewer",
                                "visibility": "private",
                                "permissions": ["compute-read"]}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            role = svc.create_role("viewer", ["compute-read"])
            assert role["name"] == "viewer"
            body = mock_req.call_args.kwargs["json"]
            assert body["role"]["name"] == "viewer"
            assert body["role"]["permissions"] == ["compute-read"]
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles" in url

    def test_get_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"role": {"id": "r1", "name": "admin",
                                "visibility": "private",
                                "permissions": ["all"]}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            role = svc.get_role("r1")
            assert role["id"] == "r1"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles/r1" in url

    def test_update_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"role": {"id": "r1", "name": "renamed",
                                "visibility": "private",
                                "permissions": ["all"]}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            role = svc.update_role("r1", "renamed")
            assert role["name"] == "renamed"
            assert mock_req.call_args[0][0] == "PUT"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles/r1" in url

    def test_delete_role(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.delete_role("r1")
            assert mock_req.call_args[0][0] == "DELETE"
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles/r1" in url

    # ── Permissions ───────────────────────────────────────────

    def test_list_permissions(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "permissions": [
                    {"name": "compute-read", "description": "Read compute"},
                    {"name": "dns-write", "description": "Write DNS"},
                ]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            perms = svc.list_permissions()
            assert len(perms) == 2
            assert perms[0]["name"] == "compute-read"
            url = mock_req.call_args[0][1]
            assert "/v3/permissions" in url

    def test_assign_permissions(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"role": {"id": "r1", "name": "myrole",
                                "visibility": "private",
                                "permissions": ["compute-read", "dns-write"]}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            role = svc.assign_permissions("r1", ["dns-write"])
            assert "dns-write" in role["permissions"]
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles/r1/assign" in url
            body = mock_req.call_args.kwargs["json"]
            assert body["permissions"] == ["dns-write"]

    def test_unassign_permissions(self, mock_client, mock_response):
        svc = IdentityService(mock_client)
        resp = mock_response(
            200,
            json_data={"role": {"id": "r1", "name": "myrole",
                                "visibility": "private",
                                "permissions": ["compute-read"]}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            role = svc.unassign_permissions("r1", ["dns-write"])
            assert "dns-write" not in role["permissions"]
            url = mock_req.call_args[0][1]
            assert "/v3/sub-users/roles/r1/unassign" in url
            body = mock_req.call_args.kwargs["json"]
            assert body["permissions"] == ["dns-write"]
