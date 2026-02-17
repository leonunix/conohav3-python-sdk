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

        GET /v3/users
        """
        url = f"{self._base_url}/v3/users"
        resp = self._get(url)
        return resp.json()["users"]

    def create_user(self, name, password, email=None, description=None):
        """Create a sub-user.

        POST /v3/users
        """
        body = {"user": {"name": name, "password": password}}
        if email:
            body["user"]["email"] = email
        if description:
            body["user"]["description"] = description
        url = f"{self._base_url}/v3/users"
        resp = self._post(url, json=body)
        return resp.json()["user"]

    def get_user(self, user_id):
        """Get sub-user details.

        GET /v3/users/{user_id}
        """
        url = f"{self._base_url}/v3/users/{user_id}"
        resp = self._get(url)
        return resp.json()["user"]

    def update_user(self, user_id, name=None, password=None, email=None,
                    description=None):
        """Update a sub-user.

        PATCH /v3/users/{user_id}
        """
        body = {"user": {}}
        if name is not None:
            body["user"]["name"] = name
        if password is not None:
            body["user"]["password"] = password
        if email is not None:
            body["user"]["email"] = email
        if description is not None:
            body["user"]["description"] = description
        url = f"{self._base_url}/v3/users/{user_id}"
        resp = self._patch(url, json=body)
        return resp.json()["user"]

    def delete_user(self, user_id):
        """Delete a sub-user.

        DELETE /v3/users/{user_id}
        """
        url = f"{self._base_url}/v3/users/{user_id}"
        self._delete(url)

    # ── Roles ─────────────────────────────────────────────────

    def list_roles(self):
        """List available roles.

        GET /v3/roles
        """
        url = f"{self._base_url}/v3/roles"
        resp = self._get(url)
        return resp.json()["roles"]

    def list_user_roles(self, project_id, user_id):
        """List roles assigned to a user on a project.

        GET /v3/projects/{project_id}/users/{user_id}/roles
        """
        url = (f"{self._base_url}/v3/projects/{project_id}"
               f"/users/{user_id}/roles")
        resp = self._get(url)
        return resp.json()["roles"]

    def assign_role(self, project_id, user_id, role_id):
        """Assign a role to a user on a project.

        PUT /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
        """
        url = (f"{self._base_url}/v3/projects/{project_id}"
               f"/users/{user_id}/roles/{role_id}")
        self._put(url)

    def unassign_role(self, project_id, user_id, role_id):
        """Remove a role from a user on a project.

        DELETE /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
        """
        url = (f"{self._base_url}/v3/projects/{project_id}"
               f"/users/{user_id}/roles/{role_id}")
        self._delete(url)

    def check_role(self, project_id, user_id, role_id):
        """Check if a user has a role on a project.

        HEAD /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
        Returns True if the role assignment exists.
        """
        url = (f"{self._base_url}/v3/projects/{project_id}"
               f"/users/{user_id}/roles/{role_id}")
        self._head(url)
        return True

    # ── Permissions ───────────────────────────────────────────

    def list_permissions(self, role_id):
        """List permissions for a role.

        GET /v3/roles/{role_id}/permissions
        """
        url = f"{self._base_url}/v3/roles/{role_id}/permissions"
        resp = self._get(url)
        return resp.json()["permissions"]

    def update_permissions(self, role_id, permissions):
        """Update permissions for a role.

        PUT /v3/roles/{role_id}/permissions
        permissions: dict of permission settings.
        """
        url = f"{self._base_url}/v3/roles/{role_id}/permissions"
        resp = self._put(url, json={"permissions": permissions})
        return resp.json()["permissions"]
