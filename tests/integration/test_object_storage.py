"""Integration tests for Object Storage API."""

import time

import pytest

from conoha.exceptions import APIError
from tests.integration.conftest import unique_name


class TestObjectStorageCRUD:
    def test_account_info(self, conoha_client):
        """Get account info."""
        try:
            info = conoha_client.object_storage.get_account_info()
            assert isinstance(info, dict)
            assert "container_count" in info
        except APIError:
            pytest.skip("Object storage not activated for this account")

    def test_object_storage_lifecycle(self, conoha_client):
        """Full object storage lifecycle:
        create container → list containers → upload object → list objects
        → download → copy → schedule deletion → delete object
        → delete container.
        """
        container = unique_name("sdk-inttest-cont")
        dst_container = unique_name("sdk-inttest-dst")
        object_name = "test-object.txt"
        dst_object = "test-object-copy.txt"
        object_data = b"Hello, ConoHa Object Storage integration test!"

        try:
            # Create container
            try:
                conoha_client.object_storage.create_container(container)
            except APIError:
                pytest.skip("Object storage not activated for this account")

            # List containers (should contain ours)
            containers_list = conoha_client.object_storage.list_containers()
            names = [c["name"] for c in containers_list]
            assert container in names

            # Upload object
            conoha_client.object_storage.upload_object(
                container,
                object_name,
                data=object_data,
                content_type="text/plain",
            )

            # List objects
            objects = conoha_client.object_storage.list_objects(container)
            obj_names = [o["name"] for o in objects]
            assert object_name in obj_names

            # Download and verify
            resp = conoha_client.object_storage.download_object(
                container, object_name
            )
            assert resp.content == object_data

            # Get object metadata
            meta = conoha_client.object_storage.get_object_metadata(
                container, object_name
            )
            assert isinstance(meta, dict)

            # Copy object (create destination container first)
            conoha_client.object_storage.create_container(dst_container)
            conoha_client.object_storage.copy_object(
                container, object_name, dst_container, dst_object
            )

            # Verify copy exists
            dst_objects = conoha_client.object_storage.list_objects(
                dst_container
            )
            dst_names = [o["name"] for o in dst_objects]
            assert dst_object in dst_names

            # Download copy and verify content
            resp_copy = conoha_client.object_storage.download_object(
                dst_container, dst_object
            )
            assert resp_copy.content == object_data

            # Schedule deletion (set very long so it doesn't actually delete)
            conoha_client.object_storage.schedule_object_deletion(
                container, object_name, seconds=86400
            )

            # Verify object still exists after scheduling
            meta_after = conoha_client.object_storage.get_object_metadata(
                container, object_name
            )
            assert isinstance(meta_after, dict)

        finally:
            # Cleanup: delete all objects and containers
            for c, objs in [(container, [object_name]),
                            (dst_container, [dst_object])]:
                for obj in objs:
                    try:
                        conoha_client.object_storage.delete_object(c, obj)
                    except Exception:
                        pass
                try:
                    conoha_client.object_storage.delete_container(c)
                except Exception:
                    pass
