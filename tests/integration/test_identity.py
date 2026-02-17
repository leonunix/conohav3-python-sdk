"""Integration tests for Identity API."""

import pytest

from tests.integration.conftest import unique_name


class TestIdentityIntegration:
    def test_authenticate(self, conoha_client):
        """Verify authentication succeeded and token is set."""
        assert conoha_client._token is not None
        assert conoha_client.tenant_id is not None
        assert conoha_client.user_id is not None

    def test_list_credentials(self, conoha_client):
        """List credentials for the authenticated user."""
        creds = conoha_client.identity.list_credentials(
            conoha_client.user_id
        )
        assert isinstance(creds, list)

    def test_credential_crud(self, conoha_client):
        """Full credential lifecycle: create → get → list → delete."""
        user_id = conoha_client.user_id
        tenant_id = conoha_client.tenant_id
        cred = None

        try:
            # Create
            cred = conoha_client.identity.create_credential(
                user_id, tenant_id
            )
            assert "access" in cred
            assert "secret" in cred
            cred_id = cred["access"]

            # Get
            fetched = conoha_client.identity.get_credential(
                user_id, cred_id
            )
            assert fetched["access"] == cred_id
            assert fetched["secret"] == cred["secret"]

            # List (should contain the new credential)
            creds = conoha_client.identity.list_credentials(user_id)
            assert any(c["access"] == cred_id for c in creds)

        finally:
            # Delete
            if cred:
                conoha_client.identity.delete_credential(
                    user_id, cred["access"]
                )

        # Verify deleted
        creds_after = conoha_client.identity.list_credentials(user_id)
        assert not any(c["access"] == cred["access"] for c in creds_after)

    # ── Sub-users ─────────────────────────────────────────────

    def test_sub_user_lifecycle(self, conoha_client):
        """Full sub-user lifecycle:
        list permissions → create role → list roles
        → create user → get user → list users → assign/unassign roles
        → update user → delete user → delete role.
        """
        role_id = None
        user_id = None

        try:
            # List permissions (should always work)
            perms = conoha_client.identity.list_permissions()
            assert isinstance(perms, list)
            assert len(perms) > 0

            # Pick the first permission for our test role
            perm_name = perms[0]["name"]

            # Create role
            role_name = unique_name("sdk-inttest-role")[:32]
            role = conoha_client.identity.create_role(
                role_name, [perm_name]
            )
            role_id = role["id"]
            assert role["name"] == role_name
            assert perm_name in role["permissions"]

            # Get role
            fetched_role = conoha_client.identity.get_role(role_id)
            assert fetched_role["id"] == role_id
            assert fetched_role["name"] == role_name

            # List roles (should contain ours)
            roles = conoha_client.identity.list_roles()
            assert any(r["id"] == role_id for r in roles)

            # Update role name
            new_role_name = unique_name("sdk-inttest-rl2")[:32]
            updated_role = conoha_client.identity.update_role(
                role_id, new_role_name
            )
            assert updated_role["name"] == new_role_name

            # Assign additional permission to role (if more than one exists)
            if len(perms) > 1:
                extra_perm = perms[1]["name"]
                role_after = conoha_client.identity.assign_permissions(
                    role_id, [extra_perm]
                )
                assert extra_perm in role_after["permissions"]

                # Unassign the extra permission
                role_after2 = conoha_client.identity.unassign_permissions(
                    role_id, [extra_perm]
                )
                assert extra_perm not in role_after2["permissions"]

            # Create sub-user
            user = conoha_client.identity.create_user(
                "TestP@ss123!", [role_id]
            )
            user_id = user["id"]
            assert user_id is not None
            assert "name" in user

            # Get sub-user
            fetched_user = conoha_client.identity.get_user(user_id)
            assert fetched_user["id"] == user_id

            # List sub-users (should contain ours)
            users = conoha_client.identity.list_users()
            assert any(u["id"] == user_id for u in users)

            # Update sub-user password
            updated_user = conoha_client.identity.update_user(
                user_id, "NewP@ss456!"
            )
            assert updated_user["id"] == user_id

            # Create a second role to test role assignment
            role2_name = unique_name("sdk-inttest-rl3")[:32]
            role2 = conoha_client.identity.create_role(
                role2_name, [perm_name]
            )
            role2_id = role2["id"]

            try:
                # Assign additional role to user
                user_after = conoha_client.identity.assign_roles(
                    user_id, [role2_id]
                )
                role_ids_after = [r["id"] for r in user_after.get("roles", [])]
                assert role2_id in role_ids_after

                # Unassign the additional role
                user_after2 = conoha_client.identity.unassign_roles(
                    user_id, [role2_id]
                )
                role_ids_after2 = [r["id"] for r in user_after2.get("roles", [])]
                assert role2_id not in role_ids_after2

            finally:
                # Cleanup role2
                try:
                    conoha_client.identity.delete_role(role2_id)
                except Exception:
                    pass

        finally:
            # Cleanup: delete user first, then role
            if user_id:
                try:
                    conoha_client.identity.delete_user(user_id)
                except Exception:
                    pass
            if role_id:
                try:
                    conoha_client.identity.delete_role(role_id)
                except Exception:
                    pass
