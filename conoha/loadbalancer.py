"""ConoHa Load Balancer API service."""

from .base import BaseService


class LoadBalancerService(BaseService):
    """Load Balancer API: load balancers, listeners, pools, members, health monitors.

    Base URL: https://lbaas.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("load_balancer")

    # ── Load Balancers ───────────────────────────────────────────

    def list_load_balancers(self):
        """List load balancers.

        GET /v2.0/lbaas/loadbalancers
        """
        url = f"{self._base_url}/v2.0/lbaas/loadbalancers"
        resp = self._get(url)
        return resp.json()["loadbalancers"]

    def get_load_balancer(self, lb_id):
        """Get load balancer details.

        GET /v2.0/lbaas/loadbalancers/{lb_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/loadbalancers/{lb_id}"
        resp = self._get(url)
        return resp.json()["loadbalancer"]

    def create_load_balancer(self, name, vip_subnet_id, admin_state_up=True):
        """Create a load balancer.

        POST /v2.0/lbaas/loadbalancers
        """
        body = {
            "loadbalancer": {
                "name": name,
                "vip_subnet_id": vip_subnet_id,
                "admin_state_up": admin_state_up,
            }
        }
        url = f"{self._base_url}/v2.0/lbaas/loadbalancers"
        resp = self._post(url, json=body)
        return resp.json()["loadbalancer"]

    def update_load_balancer(self, lb_id, name=None, admin_state_up=None):
        """Update a load balancer.

        PUT /v2.0/lbaas/loadbalancers/{lb_id}
        """
        body = {"loadbalancer": {}}
        if name is not None:
            body["loadbalancer"]["name"] = name
        if admin_state_up is not None:
            body["loadbalancer"]["admin_state_up"] = admin_state_up
        url = f"{self._base_url}/v2.0/lbaas/loadbalancers/{lb_id}"
        resp = self._put(url, json=body)
        return resp.json()["loadbalancer"]

    def delete_load_balancer(self, lb_id):
        """Delete a load balancer.

        DELETE /v2.0/lbaas/loadbalancers/{lb_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/loadbalancers/{lb_id}"
        self._delete(url)

    # ── Listeners ────────────────────────────────────────────────

    def list_listeners(self):
        """List listeners.

        GET /v2.0/lbaas/listeners
        """
        url = f"{self._base_url}/v2.0/lbaas/listeners"
        resp = self._get(url)
        return resp.json()["listeners"]

    def get_listener(self, listener_id):
        """Get listener details.

        GET /v2.0/lbaas/listeners/{listener_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/listeners/{listener_id}"
        resp = self._get(url)
        return resp.json()["listener"]

    def create_listener(self, loadbalancer_id, protocol, protocol_port,
                        name=None, connection_limit=None):
        """Create a listener.

        POST /v2.0/lbaas/listeners
        protocol: TCP, HTTP, HTTPS, UDP
        """
        body = {
            "listener": {
                "loadbalancer_id": loadbalancer_id,
                "protocol": protocol,
                "protocol_port": protocol_port,
            }
        }
        if name:
            body["listener"]["name"] = name
        if connection_limit is not None:
            body["listener"]["connection_limit"] = connection_limit
        url = f"{self._base_url}/v2.0/lbaas/listeners"
        resp = self._post(url, json=body)
        return resp.json()["listener"]

    def update_listener(self, listener_id, name=None, connection_limit=None):
        """Update a listener.

        PUT /v2.0/lbaas/listeners/{listener_id}
        """
        body = {"listener": {}}
        if name is not None:
            body["listener"]["name"] = name
        if connection_limit is not None:
            body["listener"]["connection_limit"] = connection_limit
        url = f"{self._base_url}/v2.0/lbaas/listeners/{listener_id}"
        resp = self._put(url, json=body)
        return resp.json()["listener"]

    def delete_listener(self, listener_id):
        """Delete a listener.

        DELETE /v2.0/lbaas/listeners/{listener_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/listeners/{listener_id}"
        self._delete(url)

    # ── Pools ────────────────────────────────────────────────────

    def list_pools(self):
        """List pools.

        GET /v2.0/lbaas/pools
        """
        url = f"{self._base_url}/v2.0/lbaas/pools"
        resp = self._get(url)
        return resp.json()["pools"]

    def get_pool(self, pool_id):
        """Get pool details.

        GET /v2.0/lbaas/pools/{pool_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}"
        resp = self._get(url)
        return resp.json()["pool"]

    def create_pool(self, listener_id, protocol, lb_algorithm, name=None):
        """Create a pool.

        POST /v2.0/lbaas/pools
        lb_algorithm: ROUND_ROBIN, LEAST_CONNECTIONS, SOURCE_IP
        """
        body = {
            "pool": {
                "listener_id": listener_id,
                "protocol": protocol,
                "lb_algorithm": lb_algorithm,
            }
        }
        if name:
            body["pool"]["name"] = name
        url = f"{self._base_url}/v2.0/lbaas/pools"
        resp = self._post(url, json=body)
        return resp.json()["pool"]

    def update_pool(self, pool_id, name=None, lb_algorithm=None):
        """Update a pool.

        PUT /v2.0/lbaas/pools/{pool_id}
        """
        body = {"pool": {}}
        if name is not None:
            body["pool"]["name"] = name
        if lb_algorithm is not None:
            body["pool"]["lb_algorithm"] = lb_algorithm
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}"
        resp = self._put(url, json=body)
        return resp.json()["pool"]

    def delete_pool(self, pool_id):
        """Delete a pool.

        DELETE /v2.0/lbaas/pools/{pool_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}"
        self._delete(url)

    # ── Members ──────────────────────────────────────────────────

    def list_members(self, pool_id):
        """List members in a pool.

        GET /v2.0/lbaas/pools/{pool_id}/members
        """
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}/members"
        resp = self._get(url)
        return resp.json()["members"]

    def get_member(self, pool_id, member_id):
        """Get member details.

        GET /v2.0/lbaas/pools/{pool_id}/members/{member_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}/members/{member_id}"
        resp = self._get(url)
        return resp.json()["member"]

    def create_member(self, pool_id, address, protocol_port, name=None,
                      weight=None, subnet_id=None):
        """Create a member in a pool.

        POST /v2.0/lbaas/pools/{pool_id}/members
        """
        body = {
            "member": {
                "address": address,
                "protocol_port": protocol_port,
            }
        }
        if name:
            body["member"]["name"] = name
        if weight is not None:
            body["member"]["weight"] = weight
        if subnet_id:
            body["member"]["subnet_id"] = subnet_id
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}/members"
        resp = self._post(url, json=body)
        return resp.json()["member"]

    def update_member(self, pool_id, member_id, name=None, weight=None):
        """Update a member.

        PUT /v2.0/lbaas/pools/{pool_id}/members/{member_id}
        """
        body = {"member": {}}
        if name is not None:
            body["member"]["name"] = name
        if weight is not None:
            body["member"]["weight"] = weight
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}/members/{member_id}"
        resp = self._put(url, json=body)
        return resp.json()["member"]

    def delete_member(self, pool_id, member_id):
        """Delete a member from a pool.

        DELETE /v2.0/lbaas/pools/{pool_id}/members/{member_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/pools/{pool_id}/members/{member_id}"
        self._delete(url)

    # ── Health Monitors ──────────────────────────────────────────

    def list_health_monitors(self):
        """List health monitors.

        GET /v2.0/lbaas/healthmonitors
        """
        url = f"{self._base_url}/v2.0/lbaas/healthmonitors"
        resp = self._get(url)
        return resp.json()["healthmonitors"]

    def get_health_monitor(self, health_monitor_id):
        """Get health monitor details.

        GET /v2.0/lbaas/healthmonitors/{health_monitor_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/healthmonitors/{health_monitor_id}"
        resp = self._get(url)
        return resp.json()["healthmonitor"]

    def create_health_monitor(self, pool_id, monitor_type, delay, timeout,
                              max_retries, name=None, url_path=None,
                              expected_codes=None):
        """Create a health monitor.

        POST /v2.0/lbaas/healthmonitors
        monitor_type: TCP, UDP, PING, HTTP, HTTPS
        delay: 1-180 seconds
        timeout: 1-180 seconds (must be < delay)
        """
        body = {
            "healthmonitor": {
                "pool_id": pool_id,
                "type": monitor_type,
                "delay": delay,
                "timeout": timeout,
                "max_retries": max_retries,
            }
        }
        if name:
            body["healthmonitor"]["name"] = name
        if url_path:
            body["healthmonitor"]["url_path"] = url_path
        if expected_codes:
            body["healthmonitor"]["expected_codes"] = expected_codes
        url = f"{self._base_url}/v2.0/lbaas/healthmonitors"
        resp = self._post(url, json=body)
        return resp.json()["healthmonitor"]

    def update_health_monitor(self, health_monitor_id, name=None):
        """Update a health monitor.

        PUT /v2.0/lbaas/healthmonitors/{health_monitor_id}
        """
        body = {"healthmonitor": {}}
        if name is not None:
            body["healthmonitor"]["name"] = name
        url = f"{self._base_url}/v2.0/lbaas/healthmonitors/{health_monitor_id}"
        resp = self._put(url, json=body)
        return resp.json()["healthmonitor"]

    def delete_health_monitor(self, health_monitor_id):
        """Delete a health monitor.

        DELETE /v2.0/lbaas/healthmonitors/{health_monitor_id}
        """
        url = f"{self._base_url}/v2.0/lbaas/healthmonitors/{health_monitor_id}"
        self._delete(url)
