"""Unit tests for Load Balancer API service."""

from unittest.mock import patch

import pytest

from conoha.loadbalancer import LoadBalancerService


class TestLoadBalancerService:
    def test_list_load_balancers(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            200,
            json_data={"loadbalancers": [{"id": "lb1", "name": "web-lb"}]},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            lbs = svc.list_load_balancers()
            assert lbs[0]["name"] == "web-lb"

    def test_create_load_balancer(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "loadbalancer": {"id": "lb-new", "name": "my-lb"}
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            lb = svc.create_load_balancer("my-lb", "subnet-1")
            assert lb["name"] == "my-lb"
            body = mock_req.call_args.kwargs["json"]
            assert body["loadbalancer"]["vip_subnet_id"] == "subnet-1"

    def test_create_listener(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "listener": {
                    "id": "l1",
                    "protocol": "HTTP",
                    "protocol_port": 80,
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            listener = svc.create_listener("lb1", "HTTP", 80, name="http-l")
            assert listener["protocol"] == "HTTP"

    def test_create_pool(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "pool": {
                    "id": "pool1",
                    "lb_algorithm": "ROUND_ROBIN",
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            pool = svc.create_pool("l1", "HTTP", "ROUND_ROBIN")
            assert pool["lb_algorithm"] == "ROUND_ROBIN"
            body = mock_req.call_args.kwargs["json"]
            assert body["pool"]["listener_id"] == "l1"

    def test_create_member(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "member": {
                    "id": "m1",
                    "address": "10.0.0.1",
                    "protocol_port": 8080,
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            member = svc.create_member("pool1", "10.0.0.1", 8080, weight=5)
            assert member["address"] == "10.0.0.1"

    def test_create_health_monitor(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            201,
            json_data={
                "healthmonitor": {
                    "id": "hm1",
                    "type": "HTTP",
                    "delay": 10,
                    "timeout": 5,
                }
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            hm = svc.create_health_monitor(
                "pool1", "HTTP", 10, 5, 3,
                url_path="/health", expected_codes="200",
            )
            assert hm["type"] == "HTTP"
            body = mock_req.call_args.kwargs["json"]
            assert body["healthmonitor"]["url_path"] == "/health"

    def test_delete_load_balancer(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_load_balancer("lb1")

    def test_update_load_balancer(self, mock_client, mock_response):
        svc = LoadBalancerService(mock_client)
        resp = mock_response(
            200,
            json_data={"loadbalancer": {"id": "lb1", "name": "updated"}},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            lb = svc.update_load_balancer("lb1", name="updated")
            assert lb["name"] == "updated"
