"""ConoHa Identity API service."""

from .base import BaseService


class IdentityService(BaseService):
    """Identity API: authentication and credential management.

    Base URL: https://identity.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("identity")

    # ── Credentials ──────────────────────────────────────────────

    def list_credentials(self, user_id):
        """List EC2-style credentials for a user.

        GET /v3/users/{user_id}/credentials/OS-EC2
        """
        url = f"{self._base_url}/v3/users/{user_id}/credentials/OS-EC2"
        resp = self._get(url)
        return resp.json()["credentials"]

    def create_credential(self, user_id, tenant_id):
        """Create a new EC2-style credential.

        POST /v3/users/{user_id}/credentials/OS-EC2
        Max 3 credentials per user.
        """
        url = f"{self._base_url}/v3/users/{user_id}/credentials/OS-EC2"
        resp = self._post(url, json={"tenant_id": tenant_id})
        return resp.json()["credential"]

    def get_credential(self, user_id, credential_id):
        """Get details of a specific credential.

        GET /v3/users/{user_id}/credentials/OS-EC2/{credential_id}
        """
        url = f"{self._base_url}/v3/users/{user_id}/credentials/OS-EC2/{credential_id}"
        resp = self._get(url)
        return resp.json()["credential"]

    def delete_credential(self, user_id, credential_id):
        """Delete a credential.

        DELETE /v3/users/{user_id}/credentials/OS-EC2/{credential_id}
        """
        url = f"{self._base_url}/v3/users/{user_id}/credentials/OS-EC2/{credential_id}"
        self._delete(url)
