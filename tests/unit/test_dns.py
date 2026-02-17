"""Unit tests for DNS API service."""

from unittest.mock import patch

import pytest

from conoha.dns import DNSService


class TestDNSService:
    def test_list_domains(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "domains": [
                    {"uuid": "d1", "name": "example.com.", "ttl": 3600}
                ],
                "total_count": 1,
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            domains = svc.list_domains()
            assert domains[0]["name"] == "example.com."

    def test_create_domain(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "uuid": "d-new",
                "name": "test.com.",
                "ttl": 3600,
                "email": "admin@test.com",
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            domain = svc.create_domain("test.com.", 3600, "admin@test.com")
            assert domain["name"] == "test.com."
            body = mock_req.call_args.kwargs["json"]
            assert body["email"] == "admin@test.com"

    def test_get_domain(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200,
            json_data={"uuid": "d1", "name": "example.com."},
        )
        with patch("conoha.base.requests.request", return_value=resp):
            domain = svc.get_domain("d1")
            assert domain["uuid"] == "d1"

    def test_update_domain(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200,
            json_data={"uuid": "d1", "ttl": 600},
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            domain = svc.update_domain("d1", ttl=600)
            assert domain["ttl"] == 600
            body = mock_req.call_args.kwargs["json"]
            assert body["ttl"] == 600

    def test_delete_domain(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_domain("d1")

    def test_list_records(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "records": [
                    {"id": "r1", "name": "www.example.com.", "type": "A"}
                ]
            },
        )
        with patch("conoha.base.requests.request", return_value=resp):
            records = svc.list_records("d1")
            assert records[0]["type"] == "A"

    def test_create_record(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200,
            json_data={
                "id": "r-new",
                "name": "www.test.com.",
                "type": "A",
                "data": "1.2.3.4",
            },
        )
        with patch("conoha.base.requests.request", return_value=resp) as mock_req:
            rec = svc.create_record("d1", "www.test.com.", "A", "1.2.3.4", ttl=300)
            assert rec["data"] == "1.2.3.4"
            body = mock_req.call_args.kwargs["json"]
            assert body["ttl"] == 300

    def test_update_record(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(
            200, json_data={"id": "r1", "data": "5.6.7.8"}
        )
        with patch("conoha.base.requests.request", return_value=resp):
            rec = svc.update_record("d1", "r1", data="5.6.7.8")
            assert rec["data"] == "5.6.7.8"

    def test_delete_record(self, mock_client, mock_response):
        svc = DNSService(mock_client)
        resp = mock_response(204)
        with patch("conoha.base.requests.request", return_value=resp):
            svc.delete_record("d1", "r1")
