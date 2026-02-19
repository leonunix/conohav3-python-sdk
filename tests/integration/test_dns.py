"""Integration tests for DNS API."""

import pytest

from tests.integration.conftest import unique_name

DOMAIN_NAME = "conoha.dev."


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


class TestDNSDomainOperations:
    """Test get_domain using existing conoha.dev domain."""

    def test_get_domain(self, conoha_client):
        """Get domain details."""
        domains = conoha_client.dns.list_domains()
        domain = next(
            (d for d in domains if d.get("name") == DOMAIN_NAME),
            None,
        )
        if domain is None:
            pytest.skip("conoha.dev domain not found")

        detail = conoha_client.dns.get_domain(domain["uuid"])
        assert detail["name"] == DOMAIN_NAME
        assert "uuid" in detail


class TestDNSRecordCRUD:
    """Full record lifecycle using conoha.dev domain."""

    def test_record_lifecycle(self, conoha_client):
        """Create → get → update → list → delete a DNS record."""
        # Find conoha.dev domain
        domains = conoha_client.dns.list_domains()
        domain = next(
            (d for d in domains if d.get("name") == DOMAIN_NAME),
            None,
        )
        if domain is None:
            pytest.skip("conoha.dev domain not found")

        domain_id = domain["uuid"]
        record_name = unique_name("sdk-inttest") + "." + DOMAIN_NAME
        record_id = None

        try:
            # Create A record
            record = conoha_client.dns.create_record(
                domain_id=domain_id,
                name=record_name,
                record_type="A",
                data="192.0.2.1",
                ttl=3600,
            )
            record_id = record["uuid"]
            assert record["name"] == record_name
            assert record["type"] == "A"
            assert record["data"] == "192.0.2.1"

            # Get record
            fetched = conoha_client.dns.get_record(domain_id, record_id)
            assert fetched["uuid"] == record_id
            assert fetched["name"] == record_name

            # Update record
            updated = conoha_client.dns.update_record(
                domain_id, record_id, data="192.0.2.2", ttl=7200
            )
            assert updated["data"] == "192.0.2.2"
            assert updated["ttl"] == 7200

            # List records (should contain ours)
            records = conoha_client.dns.list_records(domain_id)
            assert any(r["uuid"] == record_id for r in records)

        finally:
            # Delete record
            if record_id:
                conoha_client.dns.delete_record(domain_id, record_id)

        # Verify deleted
        records = conoha_client.dns.list_records(domain_id)
        assert not any(r["uuid"] == record_id for r in records)
