"""Integration tests for Security Group CRUD."""

import pytest

from conoha.exceptions import NotFoundError
from tests.integration.conftest import unique_name


class TestSecurityGroupCRUD:
    def test_security_group_lifecycle(self, conoha_client):
        """Full security group lifecycle:
        create SG → get → update → list → create rule → get rule → list rules
        → delete rule → delete SG → verify deleted.
        """
        sg_name = unique_name("sdk-inttest-sg")
        sg_id = None
        rule_id = None

        try:
            # Create security group
            sg = conoha_client.network.create_security_group(
                name=sg_name,
                description="integration test SG",
            )
            sg_id = sg["id"]
            assert sg["name"] == sg_name
            assert sg["description"] == "integration test SG"

            # Get
            fetched = conoha_client.network.get_security_group(sg_id)
            assert fetched["id"] == sg_id
            assert fetched["name"] == sg_name

            # Update
            new_name = sg_name + "-updated"
            updated = conoha_client.network.update_security_group(
                sg_id,
                name=new_name,
                description="updated description",
            )
            assert updated["name"] == new_name
            assert updated["description"] == "updated description"

            # List (should contain ours)
            sgs = conoha_client.network.list_security_groups()
            assert any(s["id"] == sg_id for s in sgs)

            # Create rule (allow TCP port 8080 ingress)
            rule = conoha_client.network.create_security_group_rule(
                security_group_id=sg_id,
                direction="ingress",
                ethertype="IPv4",
                protocol="tcp",
                port_range_min=8080,
                port_range_max=8080,
            )
            rule_id = rule["id"]
            assert rule["direction"] == "ingress"
            assert rule["protocol"] == "tcp"
            assert rule["port_range_min"] == 8080

            # Get rule
            fetched_rule = conoha_client.network.get_security_group_rule(
                rule_id
            )
            assert fetched_rule["id"] == rule_id

            # List rules
            rules = conoha_client.network.list_security_group_rules()
            assert any(r["id"] == rule_id for r in rules)

            # Delete rule
            conoha_client.network.delete_security_group_rule(rule_id)
            rule_id = None

        finally:
            # Cleanup
            if rule_id:
                try:
                    conoha_client.network.delete_security_group_rule(rule_id)
                except Exception:
                    pass
            if sg_id:
                try:
                    conoha_client.network.delete_security_group(sg_id)
                except Exception:
                    pass

        # Verify SG deleted
        with pytest.raises((NotFoundError, Exception)):
            conoha_client.network.get_security_group(sg_id)
