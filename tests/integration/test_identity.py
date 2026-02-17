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
