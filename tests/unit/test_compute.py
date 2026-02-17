"""Unit tests for Compute API service."""

from unittest.mock import patch, MagicMock, call

import pytest

from conoha.compute import ComputeService


class TestComputeService:
    def test_list_servers(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={"servers": [{"id": "s1", "name": "test"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            servers = svc.list_servers()
            assert len(servers) == 1
            assert servers[0]["id"] == "s1"
            args = mock_req.call_args
            assert "GET" == args[0][0]
            assert "/v2.1/servers" in args[0][1]

    def test_list_servers_detail(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "servers": [
                    {"id": "s1", "name": "test", "status": "ACTIVE"}
                ]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            servers = svc.list_servers_detail()
            assert servers[0]["status"] == "ACTIVE"

    def test_get_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={"server": {"id": "s1", "status": "ACTIVE"}},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            server = svc.get_server("s1")
            assert server["status"] == "ACTIVE"

    def test_create_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            202,
            json_data={"server": {"id": "new-s", "adminPass": "pass123"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            server = svc.create_server(
                flavor_id="flavor-1",
                admin_pass="pass123",
                volume_id="vol-1",
                instance_name_tag="my-server",
                key_name="mykey",
            )
            assert server["id"] == "new-s"
            body = mock_req.call_args.kwargs["json"]
            assert body["server"]["flavorRef"] == "flavor-1"
            assert body["server"]["key_name"] == "mykey"
            assert body["server"]["block_device_mapping_v2"][0]["uuid"] == "vol-1"

    def test_create_server_with_security_groups(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            202, json_data={"server": {"id": "s2"}}
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.create_server(
                flavor_id="f1",
                admin_pass="p",
                volume_id="v1",
                instance_name_tag="tag",
                security_groups=[{"name": "default"}],
            )
            body = mock_req.call_args.kwargs["json"]
            assert body["server"]["security_groups"] == [{"name": "default"}]

    def test_delete_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_server("s1")

    def test_start_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(202)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.start_server("s1")
            body = mock_req.call_args.kwargs["json"]
            assert "os-start" in body

    def test_stop_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(202)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.stop_server("s1")
            body = mock_req.call_args.kwargs["json"]
            assert "os-stop" in body

    def test_reboot_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(202)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.reboot_server("s1", "HARD")
            body = mock_req.call_args.kwargs["json"]
            assert body["reboot"]["type"] == "HARD"

    def test_resize_server(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(202)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.resize_server("s1", "new-flavor")
            body = mock_req.call_args.kwargs["json"]
            assert body["resize"]["flavorRef"] == "new-flavor"

    def test_confirm_resize(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(202)
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.confirm_resize("s1")
            body = mock_req.call_args.kwargs["json"]
            assert "confirmResize" in body

    def test_list_flavors(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200, json_data={"flavors": [{"id": "f1", "name": "1gb"}]}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            flavors = svc.list_flavors()
            assert flavors[0]["id"] == "f1"

    def test_list_keypairs(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200, json_data={"keypairs": [{"keypair": {"name": "mykey"}}]}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            kps = svc.list_keypairs()
            assert len(kps) == 1

    def test_create_keypair(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "keypair": {
                    "name": "newkey",
                    "public_key": "ssh-rsa ...",
                    "private_key": "-----BEGIN...",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            kp = svc.create_keypair("newkey")
            assert kp["name"] == "newkey"
            body = mock_req.call_args.kwargs["json"]
            assert body["keypair"]["name"] == "newkey"
            assert "public_key" not in body["keypair"]

    def test_create_keypair_with_public_key(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200, json_data={"keypair": {"name": "k", "public_key": "ssh-rsa abc"}}
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            svc.create_keypair("k", public_key="ssh-rsa abc")
            body = mock_req.call_args.kwargs["json"]
            assert body["keypair"]["public_key"] == "ssh-rsa abc"

    def test_get_console_url(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "remote_console": {
                    "protocol": "vnc",
                    "type": "novnc",
                    "url": "https://console.example.com/...",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            console = svc.get_console_url("s1")
            assert "url" in console

    def test_attach_volume(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "volumeAttachment": {
                    "id": "va1",
                    "volumeId": "v1",
                    "serverId": "s1",
                    "device": "/dev/vdb",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            att = svc.attach_volume("s1", "v1")
            assert att["device"] == "/dev/vdb"

    def test_get_cpu_graph(self, mock_client, mock_response):
        svc = ComputeService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "cpu": {
                    "schema": ["unixtime", "value"],
                    "data": [[1700833820, 233285714.29]],
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            cpu = svc.get_cpu_graph("s1", mode="average")
            assert cpu["schema"] == ["unixtime", "value"]
            assert mock_req.call_args.kwargs["params"]["mode"] == "average"
