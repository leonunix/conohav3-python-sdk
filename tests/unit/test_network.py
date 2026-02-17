"""Unit tests for Network API service."""

from unittest.mock import patch

import pytest

from conoha.network import NetworkService


class TestNetworkService:
    def test_list_security_groups(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "security_groups": [{"id": "sg1", "name": "default"}]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            sgs = svc.list_security_groups()
            assert sgs[0]["name"] == "default"

    def test_create_security_group(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "security_group": {"id": "sg-new", "name": "web"}
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            sg = svc.create_security_group("web", description="Web servers")
            assert sg["name"] == "web"
            body = mock_req.call_args.kwargs["json"]
            assert body["security_group"]["description"] == "Web servers"

    def test_create_security_group_rule(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "security_group_rule": {
                    "id": "r1",
                    "direction": "ingress",
                    "protocol": "tcp",
                    "port_range_min": 80,
                    "port_range_max": 80,
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            rule = svc.create_security_group_rule(
                "sg1", "ingress", protocol="tcp",
                port_range_min=80, port_range_max=80,
                remote_ip_prefix="0.0.0.0/0",
            )
            assert rule["protocol"] == "tcp"
            body = mock_req.call_args.kwargs["json"]
            assert body["security_group_rule"]["remote_ip_prefix"] == "0.0.0.0/0"

    def test_list_networks(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            200,
            json_data={"networks": [{"id": "n1", "name": "ext-net"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            nets = svc.list_networks()
            assert nets[0]["id"] == "n1"

    def test_create_network(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            201, json_data={"network": {"id": "n-new", "name": "local"}}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            net = svc.create_network("local")
            assert net["name"] == "local"

    def test_list_subnets(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            200, json_data={"subnets": [{"id": "sub1", "cidr": "10.0.0.0/24"}]}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            subs = svc.list_subnets()
            assert subs[0]["cidr"] == "10.0.0.0/24"

    def test_create_subnet(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "subnet": {"id": "s-new", "cidr": "10.0.0.0/24", "ip_version": 4}
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            sub = svc.create_subnet("n1", "10.0.0.0/24")
            assert sub["cidr"] == "10.0.0.0/24"
            body = mock_req.call_args.kwargs["json"]
            assert body["subnet"]["ip_version"] == 4

    def test_list_ports(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            200, json_data={"ports": [{"id": "p1", "status": "ACTIVE"}]}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            ports = svc.list_ports()
            assert ports[0]["status"] == "ACTIVE"

    def test_create_port(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "port": {
                    "id": "p-new",
                    "network_id": "n1",
                    "fixed_ips": [{"ip_address": "10.0.0.1"}],
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            port = svc.create_port(
                "n1",
                fixed_ips=[{"ip_address": "10.0.0.1", "subnet_id": "sub1"}],
            )
            assert port["fixed_ips"][0]["ip_address"] == "10.0.0.1"

    def test_create_additional_ip_port(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            201,
            json_data={"port": {"id": "p-addip", "status": "DOWN"}},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            port = svc.create_additional_ip_port(2)
            body = mock_req.call_args.kwargs["json"]
            assert body["allocateip"]["count"] == 2

    def test_update_port(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "port": {"id": "p1", "security_groups": ["sg1"]}
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            port = svc.update_port("p1", security_groups=["sg1"])
            assert port["security_groups"] == ["sg1"]

    def test_delete_port(self, mock_client, mock_response):
        svc = NetworkService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_port("p1")
