"""Unit tests for Image API service."""

from unittest.mock import patch

import pytest

from conoha.image import ImageService


class TestImageService:
    def test_list_images(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "images": [
                    {"id": "img1", "name": "Ubuntu", "status": "active"}
                ]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            images = svc.list_images(visibility="public", os_type="linux")
            assert len(images) == 1
            params = mock_req.call_args.kwargs["params"]
            assert params["visibility"] == "public"

    def test_get_image(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(
            200,
            json_data={"id": "img1", "name": "Ubuntu", "status": "active"},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            img = svc.get_image("img1")
            assert img["name"] == "Ubuntu"

    def test_delete_image(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_image("img1")

    def test_create_iso_image(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(
            201,
            json_data={"id": "iso1", "name": "myiso", "status": "queued"},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            img = svc.create_iso_image("myiso")
            assert img["status"] == "queued"
            body = mock_req.call_args.kwargs["json"]
            assert body["disk_format"] == "iso"
            assert body["container_format"] == "bare"

    def test_upload_iso_image(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.upload_iso_image("iso1", b"binary-data")
            args = mock_req.call_args
            assert args[0][0] == "PUT"
            assert "/v2/images/iso1/file" in args[0][1]

    def test_get_image_usage(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(
            200, json_data={"images": {"size": 200192}}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            usage = svc.get_image_usage()
            assert usage["size"] == 200192

    def test_get_image_quota(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(
            200, json_data={"quota": {"image_size": "50GB"}}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            quota = svc.get_image_quota()
            assert quota["image_size"] == "50GB"

    def test_update_image_quota(self, mock_client, mock_response):
        svc = ImageService(mock_client)
        resp = mock_response(
            200, json_data={"quota": {"image_size": "550GB"}}
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            quota = svc.update_image_quota(550)
            assert quota["image_size"] == "550GB"
            body = mock_req.call_args.kwargs["json"]
            assert body["quota"]["image_size"] == "550GB"
