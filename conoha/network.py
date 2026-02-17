"""ConoHa Network API service."""

from .base import BaseService


class NetworkService(BaseService):
    """Network API: security groups, networks, subnets, ports.

    Base URL: https://networking.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("network")

    # ── Security Groups ──────────────────────────────────────────

    def list_security_groups(self):
        """List security groups.

        GET /v2.0/security-groups
        """
        url = f"{self._base_url}/v2.0/security-groups"
        resp = self._get(url)
        return resp.json()["security_groups"]

    def create_security_group(self, name, description=None):
        """Create a security group.

        POST /v2.0/security-groups
        """
        body = {"security_group": {"name": name}}
        if description:
            body["security_group"]["description"] = description
        url = f"{self._base_url}/v2.0/security-groups"
        resp = self._post(url, json=body)
        return resp.json()["security_group"]

    def get_security_group(self, security_group_id):
        """Get security group details.

        GET /v2.0/security-groups/{security_group_id}
        """
        url = f"{self._base_url}/v2.0/security-groups/{security_group_id}"
        resp = self._get(url)
        return resp.json()["security_group"]

    def update_security_group(self, security_group_id, name=None,
                              description=None):
        """Update a security group.

        PUT /v2.0/security-groups/{security_group_id}
        """
        body = {"security_group": {}}
        if name is not None:
            body["security_group"]["name"] = name
        if description is not None:
            body["security_group"]["description"] = description
        url = f"{self._base_url}/v2.0/security-groups/{security_group_id}"
        resp = self._put(url, json=body)
        return resp.json()["security_group"]

    def delete_security_group(self, security_group_id):
        """Delete a security group.

        DELETE /v2.0/security-groups/{security_group_id}
        """
        url = f"{self._base_url}/v2.0/security-groups/{security_group_id}"
        self._delete(url)

    # ── Security Group Rules ─────────────────────────────────────

    def list_security_group_rules(self):
        """List security group rules.

        GET /v2.0/security-group-rules
        """
        url = f"{self._base_url}/v2.0/security-group-rules"
        resp = self._get(url)
        return resp.json()["security_group_rules"]

    def create_security_group_rule(
        self,
        security_group_id,
        direction,
        ethertype="IPv4",
        protocol=None,
        port_range_min=None,
        port_range_max=None,
        remote_ip_prefix=None,
    ):
        """Create a security group rule.

        POST /v2.0/security-group-rules
        """
        body = {
            "security_group_rule": {
                "security_group_id": security_group_id,
                "direction": direction,
                "ethertype": ethertype,
            }
        }
        rule = body["security_group_rule"]
        if protocol:
            rule["protocol"] = protocol
        if port_range_min is not None:
            rule["port_range_min"] = port_range_min
        if port_range_max is not None:
            rule["port_range_max"] = port_range_max
        if remote_ip_prefix:
            rule["remote_ip_prefix"] = remote_ip_prefix

        url = f"{self._base_url}/v2.0/security-group-rules"
        resp = self._post(url, json=body)
        return resp.json()["security_group_rule"]

    def get_security_group_rule(self, rule_id):
        """Get security group rule details.

        GET /v2.0/security-group-rules/{rule_id}
        """
        url = f"{self._base_url}/v2.0/security-group-rules/{rule_id}"
        resp = self._get(url)
        return resp.json()["security_group_rule"]

    def delete_security_group_rule(self, rule_id):
        """Delete a security group rule.

        DELETE /v2.0/security-group-rules/{rule_id}
        """
        url = f"{self._base_url}/v2.0/security-group-rules/{rule_id}"
        self._delete(url)

    # ── Networks ─────────────────────────────────────────────────

    def list_networks(self):
        """List networks.

        GET /v2.0/networks
        """
        url = f"{self._base_url}/v2.0/networks"
        resp = self._get(url)
        return resp.json()["networks"]

    def get_network(self, network_id):
        """Get network details.

        GET /v2.0/networks/{network_id}
        """
        url = f"{self._base_url}/v2.0/networks/{network_id}"
        resp = self._get(url)
        return resp.json()["network"]

    def create_network(self, name=None):
        """Create a local network (max 10 per account).

        POST /v2.0/networks
        """
        body = {"network": {}}
        if name:
            body["network"]["name"] = name
        url = f"{self._base_url}/v2.0/networks"
        resp = self._post(url, json=body)
        return resp.json()["network"]

    def delete_network(self, network_id):
        """Delete a network. All subnets must be removed first.

        DELETE /v2.0/networks/{network_id}
        """
        url = f"{self._base_url}/v2.0/networks/{network_id}"
        self._delete(url)

    # ── Subnets ──────────────────────────────────────────────────

    def list_subnets(self):
        """List subnets.

        GET /v2.0/subnets
        """
        url = f"{self._base_url}/v2.0/subnets"
        resp = self._get(url)
        return resp.json()["subnets"]

    def get_subnet(self, subnet_id):
        """Get subnet details.

        GET /v2.0/subnets/{subnet_id}
        """
        url = f"{self._base_url}/v2.0/subnets/{subnet_id}"
        resp = self._get(url)
        return resp.json()["subnet"]

    def create_subnet(self, network_id, cidr, ip_version=4, name=None):
        """Create a subnet.

        POST /v2.0/subnets
        """
        body = {
            "subnet": {
                "network_id": network_id,
                "cidr": cidr,
                "ip_version": ip_version,
            }
        }
        if name:
            body["subnet"]["name"] = name
        url = f"{self._base_url}/v2.0/subnets"
        resp = self._post(url, json=body)
        return resp.json()["subnet"]

    def delete_subnet(self, subnet_id):
        """Delete a subnet.

        DELETE /v2.0/subnets/{subnet_id}
        """
        url = f"{self._base_url}/v2.0/subnets/{subnet_id}"
        self._delete(url)

    # ── Ports ────────────────────────────────────────────────────

    def list_ports(self):
        """List ports.

        GET /v2.0/ports
        """
        url = f"{self._base_url}/v2.0/ports"
        resp = self._get(url)
        return resp.json()["ports"]

    def get_port(self, port_id):
        """Get port details.

        GET /v2.0/ports/{port_id}
        """
        url = f"{self._base_url}/v2.0/ports/{port_id}"
        resp = self._get(url)
        return resp.json()["port"]

    def create_port(self, network_id, fixed_ips=None, security_groups=None,
                    allowed_address_pairs=None):
        """Create a port on a local network.

        POST /v2.0/ports
        """
        body = {"port": {"network_id": network_id}}
        if fixed_ips:
            body["port"]["fixed_ips"] = fixed_ips
        if security_groups:
            body["port"]["security_groups"] = security_groups
        if allowed_address_pairs:
            body["port"]["allowed_address_pairs"] = allowed_address_pairs
        url = f"{self._base_url}/v2.0/ports"
        resp = self._post(url, json=body)
        return resp.json()["port"]

    def create_additional_ip_port(self, count, security_groups=None):
        """Create port(s) for additional IP addresses.

        POST /v2.0/allocateips
        count: 1-16
        """
        body = {"allocateip": {"count": count}}
        if security_groups:
            body["allocateip"]["security_groups"] = security_groups
        url = f"{self._base_url}/v2.0/allocateips"
        resp = self._post(url, json=body)
        return resp.json()["port"]

    def update_port(self, port_id, security_groups=None, qos_policy_id=None,
                    fixed_ips=None, allowed_address_pairs=None):
        """Update a port.

        PUT /v2.0/ports/{port_id}
        """
        body = {"port": {}}
        if security_groups is not None:
            body["port"]["security_groups"] = security_groups
        if qos_policy_id is not None:
            body["port"]["qos_policy_id"] = qos_policy_id
        if fixed_ips is not None:
            body["port"]["fixed_ips"] = fixed_ips
        if allowed_address_pairs is not None:
            body["port"]["allowed_address_pairs"] = allowed_address_pairs
        url = f"{self._base_url}/v2.0/ports/{port_id}"
        resp = self._put(url, json=body)
        return resp.json()["port"]

    def delete_port(self, port_id):
        """Delete a port. Must not be attached to a server.

        DELETE /v2.0/ports/{port_id}
        """
        url = f"{self._base_url}/v2.0/ports/{port_id}"
        self._delete(url)

    # ── QoS Policies ─────────────────────────────────────────────

    def list_qos_policies(self):
        """List QoS policies.

        GET /v2.0/qos/policies
        """
        url = f"{self._base_url}/v2.0/qos/policies"
        resp = self._get(url)
        return resp.json()["policies"]

    def get_qos_policy(self, policy_id):
        """Get QoS policy details.

        GET /v2.0/qos/policies/{policy_id}
        """
        url = f"{self._base_url}/v2.0/qos/policies/{policy_id}"
        resp = self._get(url)
        return resp.json()["policy"]
