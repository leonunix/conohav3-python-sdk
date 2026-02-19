"""Integration tests for Volume (Block Storage) API."""

import pytest

from conoha.exceptions import NotFoundError
from tests.integration.conftest import unique_name, wait_for_status


class TestVolumeTypes:
    def test_list_volume_types(self, conoha_client):
        """List volume types."""
        types = conoha_client.volume.list_volume_types()
        assert isinstance(types, list)
        assert len(types) > 0

    def test_get_volume_type(self, conoha_client):
        """Get volume type detail."""
        types = conoha_client.volume.list_volume_types()
        assert len(types) > 0
        vt = conoha_client.volume.get_volume_type(types[0]["id"])
        assert "id" in vt
        assert "name" in vt


class TestVolumeBackups:
    def test_list_backups(self, conoha_client):
        """List backups."""
        backups = conoha_client.volume.list_backups()
        assert isinstance(backups, list)

    def test_list_backups_detail(self, conoha_client):
        """List backups with full details."""
        backups = conoha_client.volume.list_backups_detail()
        assert isinstance(backups, list)


class TestVolumeCRUD:
    def test_volume_lifecycle(self, conoha_client):
        """Full volume lifecycle:
        create → wait available → get → update → list → delete → verify.
        """
        vol_name = unique_name("sdk-inttest-vol")
        volume_id = None

        try:
            # Create volume (additional volumes require 200/500/1000/5000/10000)
            vol = conoha_client.volume.create_volume(
                size=200,
                name=vol_name,
                description="integration test volume",
            )
            volume_id = vol["id"]
            assert volume_id is not None
            assert vol["size"] == 200

            # Wait for available
            wait_for_status(
                lambda: conoha_client.volume.get_volume(volume_id),
                "available",
                timeout=120,
            )

            # Get
            fetched = conoha_client.volume.get_volume(volume_id)
            assert fetched["id"] == volume_id
            assert fetched["size"] == 200

            # Update
            new_name = vol_name + "-updated"
            updated = conoha_client.volume.update_volume(
                volume_id,
                name=new_name,
                description="updated description",
            )
            assert updated["name"] == new_name

            # List (should contain ours)
            volumes = conoha_client.volume.list_volumes()
            assert any(v["id"] == volume_id for v in volumes)

            # List detail
            volumes_detail = conoha_client.volume.list_volumes_detail()
            found = [v for v in volumes_detail if v["id"] == volume_id]
            assert len(found) == 1
            assert found[0]["name"] == new_name

        finally:
            # Delete
            if volume_id:
                try:
                    conoha_client.volume.delete_volume(volume_id)
                except Exception:
                    pass
