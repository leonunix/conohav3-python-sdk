"""Integration tests for DNS API."""

import pytest


class TestDNSIntegration:
    def test_list_domains(self, conoha_client):
        """List DNS domains."""
        domains = conoha_client.dns.list_domains()
        assert isinstance(domains, list)

    def test_list_records_if_domain_exists(self, conoha_client):
        """List records if a domain exists."""
        domains = conoha_client.dns.list_domains()
        if domains:
            records = conoha_client.dns.list_records(domains[0]["uuid"])
            assert isinstance(records, list)
