"""Unit tests for Object Storage API service."""

from unittest.mock import patch, MagicMock

import pytest

from conoha.object_storage import ObjectStorageService


class TestObjectStorageService:
    def test_list_containers(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(
            200,
            json_data=[
                {"name": "container1", "count": 5, "bytes": 1024}
            ],
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            containers = svc.list_containers()
            assert containers[0]["name"] == "container1"
            url = mock_req.call_args[0][1]
            assert "/v1/AUTH_tenant-id-12345" in url

    def test_create_container(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(201)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.create_container("new-container")
            url = mock_req.call_args[0][1]
            assert "/new-container" in url
            assert mock_req.call_args[0][0] == "PUT"

    def test_delete_container(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_container("old-container")

    def test_get_container_metadata(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(
            204,
            headers={
                "x-container-object-count": "10",
                "x-container-bytes-used": "2048",
                "x-container-bytes-used-actual": "4096",
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            meta = svc.get_container_metadata("mycontainer")
            assert meta["object_count"] == "10"
            assert meta["bytes_used"] == "2048"

    def test_list_objects(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(
            200,
            json_data=[
                {
                    "name": "file.txt",
                    "hash": "abc123",
                    "bytes": 34,
                    "content_type": "text/plain",
                }
            ],
        )
        with patch("conoha.base.requests.request", return_value=resp):
            objects = svc.list_objects("mycontainer", prefix="data/")
            assert objects[0]["name"] == "file.txt"

    def test_upload_object(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(201)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.upload_object("container1", "file.txt", b"hello world")
            url = mock_req.call_args[0][1]
            assert "/container1/file.txt" in url
            assert mock_req.call_args[0][0] == "PUT"

    def test_download_object(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(200)
        resp.content = b"file-content"
        with patch("conoha.base.requests.request", return_value=resp):
            result = svc.download_object("container1", "file.txt")
            assert result.content == b"file-content"

    def test_delete_object(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_object("container1", "file.txt")

    def test_set_account_quota(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.set_account_quota(100)
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Account-Meta-Quota-Giga-Bytes"] == "100"

    def test_get_object_metadata(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(
            200,
            headers={
                "Content-Type": "text/plain",
                "Content-Length": "100",
                "Last-Modified": "Thu, 01 Jan 2026 00:00:00 GMT",
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            meta = svc.get_object_metadata("container1", "file.txt")
            assert meta["Content-Type"] == "text/plain"
