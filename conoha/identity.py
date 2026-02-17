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

    # ── Token Management ──────────────────────────────────────

    def validate_token(self, token):
        """Validate a token and get its metadata.

        GET /v3/auth/tokens
        """
        url = f"{self._base_url}/v3/auth/tokens"
        resp = self._get(url, extra_headers={"X-Subject-Token": token})
        return resp.json()["token"]

    def get_token_info(self):
        """Get info about the current token.

        GET /v3/auth/tokens
        """
        url = f"{self._base_url}/v3/auth/tokens"
        resp = self._get(url, extra_headers={"X-Subject-Token": self._token})
        return resp.json()["token"]

    def revoke_token(self, token):
        """Revoke a token.

        DELETE /v3/auth/tokens
        """
        url = f"{self._base_url}/v3/auth/tokens"
        self._delete(url, extra_headers={"X-Subject-Token": token})

    # ── Sub-users ─────────────────────────────────────────────

    def list_users(self):
        """List sub-users.

        GET /v3/sub-users
        """
        url = f"{self._base_url}/v3/sub-users"
        resp = self._get(url)
        return resp.json()["users"]

    def create_user(self, password, roles):
        """Create a sub-user.

        POST /v3/sub-users
        password: 9-70 chars, must include lowercase, uppercase, and numbers/symbols.
        roles: list of role IDs to assign. At least one required. Max 500.
        Max 10 sub-users per account.
        """
        body = {"user": {"password": password, "roles": roles}}
        url = f"{self._base_url}/v3/sub-users"
        resp = self._post(url, json=body)
        return resp.json()["user"]

    def get_user(self, subuser_id):
        """Get sub-user details.

        GET /v3/sub-users/{subuser_id}
        """
        url = f"{self._base_url}/v3/sub-users/{subuser_id}"
        resp = self._get(url)
        return resp.json()["user"]

    def update_user(self, subuser_id, password):
        """Update a sub-user's password.

        PUT /v3/sub-users/{subuser_id}
        """
        body = {"user": {"password": password}}
        url = f"{self._base_url}/v3/sub-users/{subuser_id}"
        resp = self._put(url, json=body)
        return resp.json()["user"]

    def delete_user(self, subuser_id):
        """Delete a sub-user.

        DELETE /v3/sub-users/{subuser_id}
        """
        url = f"{self._base_url}/v3/sub-users/{subuser_id}"
        self._delete(url)

    def assign_roles(self, subuser_id, role_ids):
        """Assign roles to a sub-user.

        POST /v3/sub-users/{subuser_id}/assign
        role_ids: list of role IDs. Max 500 assignments per sub-user.
        """
        url = f"{self._base_url}/v3/sub-users/{subuser_id}/assign"
        resp = self._post(url, json={"roles": role_ids})
        return resp.json()["user"]

    def unassign_roles(self, subuser_id, role_ids):
        """Remove roles from a sub-user.

        POST /v3/sub-users/{subuser_id}/unassign
        At least one role must remain assigned.
        """
        url = f"{self._base_url}/v3/sub-users/{subuser_id}/unassign"
        resp = self._post(url, json={"roles": role_ids})
        return resp.json()["user"]

    # ── Roles ─────────────────────────────────────────────────

    def list_roles(self):
        """List available roles.

        GET /v3/sub-users/roles
        """
        url = f"{self._base_url}/v3/sub-users/roles"
        resp = self._get(url)
        return resp.json()["roles"]

    def create_role(self, name, permissions):
        """Create a role.

        POST /v3/sub-users/roles
        name: 1-32 chars, alphanumeric, underscores, hyphens.
        permissions: list of permission name strings.
        """
        body = {"role": {"name": name, "permissions": permissions}}
        url = f"{self._base_url}/v3/sub-users/roles"
        resp = self._post(url, json=body)
        return resp.json()["role"]

    def get_role(self, role_id):
        """Get role details.

        GET /v3/sub-users/roles/{role_id}
        """
        url = f"{self._base_url}/v3/sub-users/roles/{role_id}"
        resp = self._get(url)
        return resp.json()["role"]

    def update_role(self, role_id, name):
        """Update a role's name.

        PUT /v3/sub-users/roles/{role_id}
        """
        body = {"role": {"name": name}}
        url = f"{self._base_url}/v3/sub-users/roles/{role_id}"
        resp = self._put(url, json=body)
        return resp.json()["role"]

    def delete_role(self, role_id):
        """Delete a role. Cannot delete roles assigned to sub-users.

        DELETE /v3/sub-users/roles/{role_id}
        """
        url = f"{self._base_url}/v3/sub-users/roles/{role_id}"
        self._delete(url)

    # ── Permissions ───────────────────────────────────────────

    def list_permissions(self):
        """List all available permissions.

        GET /v3/permissions
        """
        url = f"{self._base_url}/v3/permissions"
        resp = self._get(url)
        return resp.json()["permissions"]

    def assign_permissions(self, role_id, permissions):
        """Assign permissions to a role.

        POST /v3/sub-users/roles/{role_id}/assign
        permissions: list of permission name strings.
        """
        url = f"{self._base_url}/v3/sub-users/roles/{role_id}/assign"
        resp = self._post(url, json={"permissions": permissions})
        return resp.json()["role"]

    def unassign_permissions(self, role_id, permissions):
        """Remove permissions from a role.

        POST /v3/sub-users/roles/{role_id}/unassign
        At least one permission must remain assigned.
        """
        url = f"{self._base_url}/v3/sub-users/roles/{role_id}/unassign"
        resp = self._post(url, json={"permissions": permissions})
        return resp.json()["role"]
