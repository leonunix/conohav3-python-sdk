"""Unit tests for Volume (Block Storage) API service."""

from unittest.mock import patch

import pytest

from conoha.volume import VolumeService


class TestVolumeService:
    def test_list_volumes(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            200, json_data={"volumes": [{"id": "v1", "size": 100}]}
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            vols = svc.list_volumes()
            assert len(vols) == 1
            url = mock_req.call_args[0][1]
            assert "/v3/tenant-id-12345/volumes" in url

    def test_list_volumes_detail(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "volumes": [{"id": "v1", "size": 100, "status": "in-use"}]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            vols = svc.list_volumes_detail()
            assert vols[0]["status"] == "in-use"

    def test_get_volume(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            200, json_data={"volume": {"id": "v1", "size": 100}}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            vol = svc.get_volume("v1")
            assert vol["size"] == 100

    def test_create_volume(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            200, json_data={"volume": {"id": "v-new", "size": 200}}
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            vol = svc.create_volume(200, name="myvolume", volume_type="boot")
            assert vol["id"] == "v-new"
            body = mock_req.call_args.kwargs["json"]
            assert body["volume"]["size"] == 200
            assert body["volume"]["name"] == "myvolume"

    def test_delete_volume(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_volume("v1")

    def test_save_volume_as_image(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            202,
            json_data={
                "os-volume_upload_image": {
                    "id": "v1",
                    "image_id": "img-1",
                    "image_name": "saved-image",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            result = svc.save_volume_as_image("v1", "saved-image")
            assert result["image_name"] == "saved-image"
            body = mock_req.call_args.kwargs["json"]
            assert body["os-volume_upload_image"]["image_name"] == "saved-image"

    def test_list_volume_types(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            200, json_data={"volume_types": [{"id": "t1", "name": "boot"}]}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            types = svc.list_volume_types()
            assert types[0]["name"] == "boot"

    def test_list_backups(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            200, json_data={"backups": [{"id": "b1"}]}
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            backups = svc.list_backups(limit=10, offset=0)
            assert len(backups) == 1
            assert mock_req.call_args.kwargs["params"]["limit"] == 10

    def test_enable_auto_backup(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "backup": {"instance_uuid": "s1", "id": "backup-1"}
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            result = svc.enable_auto_backup("s1")
            assert result["instance_uuid"] == "s1"
            body = mock_req.call_args.kwargs["json"]
            assert body["backup"]["instance_uuid"] == "s1"

    def test_restore_backup(self, mock_client, mock_response):
        svc = VolumeService(mock_client)
        resp = mock_response(
            202,
            json_data={
                "restore": {
                    "backup_id": "b1",
                    "volume_id": "v1",
                    "volume_name": "vol",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            result = svc.restore_backup("b1", "v1")
            assert result["backup_id"] == "b1"
