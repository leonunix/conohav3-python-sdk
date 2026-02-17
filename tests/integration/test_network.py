"""Integration tests for Network CRUD (networks, subnets, ports, QoS)."""

import pytest

from conoha.exceptions import NotFoundError
from tests.integration.conftest import unique_name


class TestNetworkReadOnly:
    def test_list_security_groups(self, conoha_client):
        """List security groups."""
        sgs = conoha_client.network.list_security_groups()
        assert isinstance(sgs, list)
        # Default security group should always exist
        assert len(sgs) > 0

    def test_list_security_group_rules(self, conoha_client):
        """List security group rules."""
        rules = conoha_client.network.list_security_group_rules()
        assert isinstance(rules, list)

    def test_list_networks(self, conoha_client):
        """List networks."""
        networks = conoha_client.network.list_networks()
        assert isinstance(networks, list)

    def test_list_subnets(self, conoha_client):
        """List subnets."""
        subnets = conoha_client.network.list_subnets()
        assert isinstance(subnets, list)

    def test_list_ports(self, conoha_client):
        """List ports."""
        ports = conoha_client.network.list_ports()
        assert isinstance(ports, list)

    def test_get_network_detail(self, conoha_client):
        """Get detail of first network."""
        networks = conoha_client.network.list_networks()
        if networks:
            net = conoha_client.network.get_network(networks[0]["id"])
            assert "id" in net


class TestNetworkCRUD:
    def test_network_subnet_port_lifecycle(self, conoha_client):
        """Full network lifecycle:
        create network → get → list
        → create subnet → get → list
        → create port → get → update → list
        → delete port → delete subnet → delete network → verify deleted.
        """
        net_name = unique_name("sdk-inttest-net")
        network_id = None
        subnet_id = None
        port_id = None

        try:
            # Create network
            net = conoha_client.network.create_network(name=net_name)
            network_id = net["id"]
            assert network_id is not None

            # Get network
            fetched_net = conoha_client.network.get_network(network_id)
            assert fetched_net["id"] == network_id

            # List networks (should contain ours)
            nets = conoha_client.network.list_networks()
            assert any(n["id"] == network_id for n in nets)

            # Create subnet
            subnet = conoha_client.network.create_subnet(
                network_id=network_id,
                cidr="192.168.100.0/24",
                ip_version=4,
                name=unique_name("sdk-inttest-sub"),
            )
            subnet_id = subnet["id"]
            assert subnet["network_id"] == network_id
            assert subnet["cidr"] == "192.168.100.0/24"

            # Get subnet
            fetched_sub = conoha_client.network.get_subnet(subnet_id)
            assert fetched_sub["id"] == subnet_id

            # List subnets (should contain ours)
            subs = conoha_client.network.list_subnets()
            assert any(s["id"] == subnet_id for s in subs)

            # Create port
            port = conoha_client.network.create_port(
                network_id=network_id,
            )
            port_id = port["id"]
            assert port["network_id"] == network_id

            # Get port
            fetched_port = conoha_client.network.get_port(port_id)
            assert fetched_port["id"] == port_id

            # Update port (e.g. change security groups)
            updated_port = conoha_client.network.update_port(
                port_id,
                security_groups=[],
            )
            assert updated_port["id"] == port_id

            # List ports (should contain ours)
            ports = conoha_client.network.list_ports()
            assert any(p["id"] == port_id for p in ports)

        finally:
            # Cleanup in reverse order
            if port_id:
                try:
                    conoha_client.network.delete_port(port_id)
                except Exception:
                    pass
            if subnet_id:
                try:
                    conoha_client.network.delete_subnet(subnet_id)
                except Exception:
                    pass
            if network_id:
                try:
                    conoha_client.network.delete_network(network_id)
                except Exception:
                    pass

        # Verify network deleted
        with pytest.raises((NotFoundError, Exception)):
            conoha_client.network.get_network(network_id)


class TestQoSPolicy:
    def test_list_qos_policies(self, conoha_client):
        """List QoS policies."""
        policies = conoha_client.network.list_qos_policies()
        assert isinstance(policies, list)
        # ConoHa should have at least some QoS policies
        if policies:
            policy = conoha_client.network.get_qos_policy(policies[0]["id"])
            assert "id" in policy
