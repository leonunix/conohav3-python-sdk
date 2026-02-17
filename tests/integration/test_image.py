"""Integration tests for Image API."""

import pytest


class TestImageIntegration:
    def test_list_images(self, conoha_client):
        """List images."""
        images = conoha_client.image.list_images()
        assert isinstance(images, list)
        assert len(images) > 0

    def test_list_images_public(self, conoha_client):
        """List public images only."""
        images = conoha_client.image.list_images(visibility="public")
        assert isinstance(images, list)
        assert len(images) > 0

    def test_get_image(self, conoha_client):
        """Get image detail for the first available image."""
        images = conoha_client.image.list_images(limit=1)
        assert len(images) > 0
        image = conoha_client.image.get_image(images[0]["id"])
        assert "id" in image
        assert "name" in image
        assert "status" in image

    def test_get_image_quota(self, conoha_client):
        """Get image storage quota."""
        quota = conoha_client.image.get_image_quota()
        assert isinstance(quota, dict)
        assert "image_size" in quota

    def test_get_image_usage(self, conoha_client):
        """Get image storage usage."""
        usage = conoha_client.image.get_image_usage()
        assert isinstance(usage, dict)
        assert "size" in usage
