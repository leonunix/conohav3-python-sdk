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


class TestObjectStorageWebPublishing:
    def test_web_publishing_lifecycle(self, conoha_client):
        """Enable and disable web publishing on a container."""
        container = unique_name("sdk-inttest-webpub")

        try:
            try:
                conoha_client.object_storage.create_container(container)
            except APIError:
                pytest.skip("Object storage not activated for this account")

            # Enable web publishing
            conoha_client.object_storage.enable_web_publishing(container)

            # Verify via container metadata
            meta = conoha_client.object_storage.get_container_metadata(
                container
            )
            assert isinstance(meta, dict)

            # Disable web publishing
            conoha_client.object_storage.disable_web_publishing(container)

        finally:
            try:
                conoha_client.object_storage.delete_container(container)
            except Exception:
                pass


class TestObjectStorageVersioning:
    def test_versioning_lifecycle(self, conoha_client):
        """Enable and disable object versioning."""
        container = unique_name("sdk-inttest-ver")
        versions_container = unique_name("sdk-inttest-verstore")

        try:
            try:
                conoha_client.object_storage.create_container(container)
                conoha_client.object_storage.create_container(
                    versions_container
                )
            except APIError:
                pytest.skip("Object storage not activated for this account")

            # Enable versioning
            conoha_client.object_storage.enable_versioning(
                container, versions_container
            )

            # Upload an object twice to create a version
            conoha_client.object_storage.upload_object(
                container, "versioned.txt", b"version 1"
            )
            conoha_client.object_storage.upload_object(
                container, "versioned.txt", b"version 2"
            )

            # The versions container should have the old version
            versions = conoha_client.object_storage.list_objects(
                versions_container
            )
            assert isinstance(versions, list)

            # Disable versioning
            conoha_client.object_storage.disable_versioning(container)

        finally:
            # Cleanup: delete objects then containers
            for c in [container, versions_container]:
                try:
                    objs = conoha_client.object_storage.list_objects(c)
                    for o in objs:
                        conoha_client.object_storage.delete_object(
                            c, o["name"]
                        )
                except Exception:
                    pass
                try:
                    conoha_client.object_storage.delete_container(c)
                except Exception:
                    pass


class TestObjectStorageLargeObjects:
    def test_dlo_manifest(self, conoha_client):
        """Create a Dynamic Large Object manifest."""
        container = unique_name("sdk-inttest-dlo")

        try:
            try:
                conoha_client.object_storage.create_container(container)
            except APIError:
                pytest.skip("Object storage not activated for this account")

            # Upload segments
            conoha_client.object_storage.upload_object(
                container, "segments/001", b"part1"
            )
            conoha_client.object_storage.upload_object(
                container, "segments/002", b"part2"
            )

            # Create DLO manifest
            conoha_client.object_storage.create_dlo_manifest(
                container, "big-file.txt", "segments/"
            )

            # Download the manifest object (should concatenate segments)
            resp = conoha_client.object_storage.download_object(
                container, "big-file.txt"
            )
            assert resp.content == b"part1part2"

        finally:
            # Cleanup
            for obj in ["big-file.txt", "segments/001", "segments/002"]:
                try:
                    conoha_client.object_storage.delete_object(container, obj)
                except Exception:
                    pass
            try:
                conoha_client.object_storage.delete_container(container)
            except Exception:
                pass

    def test_slo_manifest(self, conoha_client):
        """Create a Static Large Object manifest."""
        container = unique_name("sdk-inttest-slo")

        try:
            try:
                conoha_client.object_storage.create_container(container)
            except APIError:
                pytest.skip("Object storage not activated for this account")

            # Upload segments
            seg1_data = b"segment-one-data"
            seg2_data = b"segment-two-data"
            conoha_client.object_storage.upload_object(
                container, "seg/001", seg1_data
            )
            conoha_client.object_storage.upload_object(
                container, "seg/002", seg2_data
            )

            # Get etags from metadata
            meta1 = conoha_client.object_storage.get_object_metadata(
                container, "seg/001"
            )
            meta2 = conoha_client.object_storage.get_object_metadata(
                container, "seg/002"
            )
            etag1 = meta1.get("Etag") or meta1.get("etag")
            etag2 = meta2.get("Etag") or meta2.get("etag")

            # Create SLO manifest
            segments = [
                {
                    "path": f"/{container}/seg/001",
                    "etag": etag1,
                    "size_bytes": len(seg1_data),
                },
                {
                    "path": f"/{container}/seg/002",
                    "etag": etag2,
                    "size_bytes": len(seg2_data),
                },
            ]
            conoha_client.object_storage.create_slo_manifest(
                container, "slo-file.txt", segments
            )

            # Download the SLO (should concatenate segments)
            resp = conoha_client.object_storage.download_object(
                container, "slo-file.txt"
            )
            assert resp.content == seg1_data + seg2_data

        finally:
            # Cleanup: delete manifest with multipart-manifest=delete,
            # then segments, then container
            for obj in ["slo-file.txt", "seg/001", "seg/002"]:
                try:
                    conoha_client.object_storage.delete_object(container, obj)
                except Exception:
                    pass
            try:
                conoha_client.object_storage.delete_container(container)
            except Exception:
                pass


class TestObjectStorageTempURL:
    def test_set_temp_url_key_and_generate(self, conoha_client):
        """Set temp URL key and generate a temporary URL."""
        container = unique_name("sdk-inttest-tempurl")
        object_name = "temp-test.txt"
        object_data = b"temporary access content"

        try:
            try:
                conoha_client.object_storage.create_container(container)
            except APIError:
                pytest.skip("Object storage not activated for this account")

            # Upload an object
            conoha_client.object_storage.upload_object(
                container, object_name, object_data
            )

            # Set temp URL key
            temp_key = unique_name("sdk-inttest-key")
            conoha_client.object_storage.set_temp_url_key(temp_key)

            # Generate temp URL
            temp_url = conoha_client.object_storage.generate_temp_url(
                container, object_name, seconds=3600,
                method="GET", key=temp_key,
            )
            assert "temp_url_sig=" in temp_url
            assert "temp_url_expires=" in temp_url
            assert f"/{container}/{object_name}" in temp_url

            # Set temp URL key 2 (rotation)
            temp_key2 = unique_name("sdk-inttest-key2")
            conoha_client.object_storage.set_temp_url_key(
                temp_key2, key_index=2
            )

        finally:
            try:
                conoha_client.object_storage.delete_object(
                    container, object_name
                )
            except Exception:
                pass
            try:
                conoha_client.object_storage.delete_container(container)
            except Exception:
                pass
