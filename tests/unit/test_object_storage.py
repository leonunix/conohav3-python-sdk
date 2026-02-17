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

    # ── Web Publishing ────────────────────────────────────────

    def test_enable_web_publishing(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.enable_web_publishing("public-container")
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Container-Read"] == ".r:*"

    def test_disable_web_publishing(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.disable_web_publishing("public-container")
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Container-Read"] == ""

    # ── Versioning ────────────────────────────────────────────

    def test_enable_versioning(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.enable_versioning("mycontainer", "versions-container")
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Versions-Location"] == "versions-container"

    def test_disable_versioning(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.disable_versioning("mycontainer")
            headers = mock_req.call_args.kwargs["headers"]
            assert "X-Remove-Versions-Location" in headers

    # ── Large Objects ─────────────────────────────────────────

    def test_create_dlo_manifest(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(201)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.create_dlo_manifest("mycontainer", "big-file", "segments/")
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Object-Manifest"] == "mycontainer/segments/"
            assert mock_req.call_args[0][0] == "PUT"

    def test_create_slo_manifest(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(201)
        segments = [
            {"path": "/c/seg1", "etag": "abc", "size_bytes": 1024},
            {"path": "/c/seg2", "etag": "def", "size_bytes": 512},
        ]
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.create_slo_manifest("mycontainer", "big-file", segments)
            assert mock_req.call_args[0][0] == "PUT"
            params = mock_req.call_args.kwargs.get("params", {})
            assert params["multipart-manifest"] == "put"

    # ── Temporary URL ─────────────────────────────────────────

    def test_set_temp_url_key(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.set_temp_url_key("my-secret-key")
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Account-Meta-Temp-URL-Key"] == "my-secret-key"

    def test_set_temp_url_key_index_2(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.set_temp_url_key("key2", key_index=2)
            headers = mock_req.call_args.kwargs["headers"]
            assert headers["X-Account-Meta-Temp-URL-Key-2"] == "key2"

    def test_generate_temp_url(self, mock_client, mock_response):
        svc = ObjectStorageService(mock_client)
        url = svc.generate_temp_url("container1", "file.txt", 3600,
                                     method="GET", key="secret")
        assert "temp_url_sig=" in url
        assert "temp_url_expires=" in url
        assert "/container1/file.txt" in url

    def test_generate_temp_url_requires_key(self, mock_client):
        svc = ObjectStorageService(mock_client)
        with pytest.raises(ValueError, match="key is required"):
            svc.generate_temp_url("c", "o", 60)
