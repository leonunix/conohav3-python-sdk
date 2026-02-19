"""ConoHa Volume (Block Storage) API service."""

from .base import BaseService


class VolumeService(BaseService):
    """Block Storage API: volumes, volume types, backups.

    Base URL: https://block-storage.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("block_storage")

    def _project_url(self, path=""):
        return f"{self._base_url}/v3/{self._tenant_id}{path}"

    # ── Volumes ──────────────────────────────────────────────────

    def list_volumes(self):
        """List volumes (minimal info).

        GET /v3/{project_id}/volumes
        """
        resp = self._get(self._project_url("/volumes"))
        return resp.json()["volumes"]

    def list_volumes_detail(self):
        """List volumes with full details.

        GET /v3/{project_id}/volumes/detail
        """
        resp = self._get(self._project_url("/volumes/detail"))
        return resp.json()["volumes"]

    def get_volume(self, volume_id):
        """Get volume details.

        GET /v3/{project_id}/volumes/{volume_id}
        """
        resp = self._get(self._project_url(f"/volumes/{volume_id}"))
        return resp.json()["volume"]

    def create_volume(self, size, name=None, description=None, volume_type=None,
                      image_ref=None, source_volid=None, snapshot_id=None):
        """Create a new volume.

        POST /v3/{project_id}/volumes
        """
        body = {"volume": {"size": size}}
        if name:
            body["volume"]["name"] = name
        if description:
            body["volume"]["description"] = description
        if volume_type:
            body["volume"]["volume_type"] = volume_type
        if image_ref:
            body["volume"]["imageRef"] = image_ref
        if source_volid:
            body["volume"]["source_volid"] = source_volid
        if snapshot_id:
            body["volume"]["snapshot_id"] = snapshot_id
        resp = self._post(self._project_url("/volumes"), json=body)
        return resp.json()["volume"]

    def update_volume(self, volume_id, name=None, description=None):
        """Update a volume.

        PUT /v3/{project_id}/volumes/{volume_id}
        """
        body = {"volume": {}}
        if name is not None:
            body["volume"]["name"] = name
        if description is not None:
            body["volume"]["description"] = description
        resp = self._put(
            self._project_url(f"/volumes/{volume_id}"), json=body
        )
        return resp.json()["volume"]

    def delete_volume(self, volume_id):
        """Delete a volume.

        DELETE /v3/{project_id}/volumes/{volume_id}
        """
        self._delete(self._project_url(f"/volumes/{volume_id}"))

    def save_volume_as_image(self, volume_id, image_name):
        """Save a volume as an image.

        POST /v3/{project_id}/volumes/{volume_id}/action
        """
        body = {
            "os-volume_upload_image": {
                "image_name": image_name,
                "disk_format": "qcow2",
                "container_format": "ovf",
            }
        }
        resp = self._post(
            self._project_url(f"/volumes/{volume_id}/action"), json=body
        )
        return resp.json()["os-volume_upload_image"]

    # ── Volume Types ─────────────────────────────────────────────

    def list_volume_types(self):
        """List volume types.

        GET /v3/{project_id}/types
        """
        resp = self._get(self._project_url("/types"))
        return resp.json()["volume_types"]

    def get_volume_type(self, type_id):
        """Get volume type details.

        GET /v3/{project_id}/types/{type_id}
        """
        resp = self._get(self._project_url(f"/types/{type_id}"))
        return resp.json()["volume_type"]

    # ── Backups ──────────────────────────────────────────────────

    def list_backups(self, limit=None, offset=None, sort=None):
        """List backups (minimal info).

        GET /v3/{project_id}/backups
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort:
            params["sort"] = sort
        resp = self._get(self._project_url("/backups"), params=params)
        return resp.json()["backups"]

    def list_backups_detail(self, limit=None, offset=None, sort=None):
        """List backups with full details.

        GET /v3/{project_id}/backups/detail
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort:
            params["sort"] = sort
        resp = self._get(self._project_url("/backups/detail"), params=params)
        return resp.json()["backups"]

    def get_backup(self, backup_id):
        """Get backup details.

        GET /v3/{project_id}/backups/{backup_id}
        """
        resp = self._get(self._project_url(f"/backups/{backup_id}"))
        return resp.json()["backup"]

    def enable_auto_backup(self, server_id, schedule=None, retention=None):
        """Enable auto-backup for a server's volumes.

        POST /v3/{project_id}/backups

        Args:
            server_id: The server (instance) UUID.
            schedule: Backup frequency - "daily" or "weekly" (default: "weekly").
            retention: Retention period in days (14-30).
                Only effective for daily backups.
        """
        body = {"backup": {"instance_uuid": server_id}}
        if schedule is not None:
            body["backup"]["schedule"] = schedule
        if retention is not None:
            body["backup"]["retention"] = retention
        resp = self._post(self._project_url("/backups"), json=body)
        return resp.json()["backup"]

    def update_backup_retention(self, server_id, retention):
        """Update retention period for daily backup.

        PUT /v3/{project_id}/backups/{server_id}

        Requires an active daily backup subscription.

        Args:
            server_id: The server (instance) UUID.
            retention: New retention period in days (14-30).
        """
        body = {"backup": {"retention": retention}}
        resp = self._put(
            self._project_url(f"/backups/{server_id}"), json=body
        )
        return resp.json()["backup"]

    def disable_auto_backup(self, server_id):
        """Disable auto-backup for a server.

        Cancels both weekly and daily backup subscriptions if both are active.

        DELETE /v3/{project_id}/backups/{server_id}
        """
        self._delete(self._project_url(f"/backups/{server_id}"))

    def restore_backup(self, backup_id, volume_id):
        """Restore a backup to a volume.

        POST /v3/{project_id}/backups/{backup_id}/restore
        """
        body = {"restore": {"volume_id": volume_id}}
        resp = self._post(
            self._project_url(f"/backups/{backup_id}/restore"), json=body
        )
        return resp.json()["restore"]
