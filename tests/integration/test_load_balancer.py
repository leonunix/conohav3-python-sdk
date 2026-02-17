"""Integration tests for Load Balancer API."""

import time

import pytest

from tests.integration.conftest import (
    unique_name,
    wait_for_lb_status,
)


class TestLoadBalancerCRUD:
    def test_load_balancer_lifecycle(self, conoha_client):
        """Full load balancer lifecycle:
        create LB → wait ACTIVE
        → create listener → create pool → create health monitor
        → delete health monitor → delete pool → delete listener
        → delete LB → verify.
        """
        lb_name = unique_name("sdk-inttest-lb")
        lb_id = None
        listener_id = None
        pool_id = None
        hm_id = None

        try:
            # Need a subnet for the VIP - find an existing one
            subnets = conoha_client.network.list_subnets()
            if not subnets:
                pytest.skip("No subnets available for LB VIP")
            vip_subnet_id = subnets[0]["id"]

            # Create load balancer
            lb = conoha_client.load_balancer.create_load_balancer(
                name=lb_name,
                vip_subnet_id=vip_subnet_id,
            )
            lb_id = lb["id"]
            assert lb_id is not None
            assert lb["name"] == lb_name

            # Wait for ACTIVE
            wait_for_lb_status(conoha_client, lb_id, "ACTIVE", timeout=300)

            # Get LB
            fetched = conoha_client.load_balancer.get_load_balancer(lb_id)
            assert fetched["id"] == lb_id

            # List LBs
            lbs = conoha_client.load_balancer.list_load_balancers()
            assert any(l["id"] == lb_id for l in lbs)

            # Update LB
            updated = conoha_client.load_balancer.update_load_balancer(
                lb_id, name=lb_name + "-updated"
            )
            assert updated["name"] == lb_name + "-updated"
            wait_for_lb_status(conoha_client, lb_id, "ACTIVE")

            # Create listener
            listener = conoha_client.load_balancer.create_listener(
                loadbalancer_id=lb_id,
                protocol="TCP",
                protocol_port=80,
                name=unique_name("sdk-inttest-lis"),
            )
            listener_id = listener["id"]
            assert listener_id is not None
            wait_for_lb_status(conoha_client, lb_id, "ACTIVE")

            # Get listener
            fetched_lis = conoha_client.load_balancer.get_listener(listener_id)
            assert fetched_lis["id"] == listener_id

            # List listeners
            listeners = conoha_client.load_balancer.list_listeners()
            assert any(l["id"] == listener_id for l in listeners)

            # Create pool
            pool = conoha_client.load_balancer.create_pool(
                listener_id=listener_id,
                protocol="TCP",
                lb_algorithm="ROUND_ROBIN",
                name=unique_name("sdk-inttest-pool"),
            )
            pool_id = pool["id"]
            assert pool_id is not None
            wait_for_lb_status(conoha_client, lb_id, "ACTIVE")

            # Get pool
            fetched_pool = conoha_client.load_balancer.get_pool(pool_id)
            assert fetched_pool["id"] == pool_id

            # List pools
            pools = conoha_client.load_balancer.list_pools()
            assert any(p["id"] == pool_id for p in pools)

            # Create health monitor
            hm = conoha_client.load_balancer.create_health_monitor(
                pool_id=pool_id,
                monitor_type="TCP",
                delay=10,
                timeout=5,
                max_retries=3,
                name=unique_name("sdk-inttest-hm"),
            )
            hm_id = hm["id"]
            assert hm_id is not None
            wait_for_lb_status(conoha_client, lb_id, "ACTIVE")

            # Get health monitor
            fetched_hm = conoha_client.load_balancer.get_health_monitor(hm_id)
            assert fetched_hm["id"] == hm_id

            # List health monitors
            hms = conoha_client.load_balancer.list_health_monitors()
            assert any(h["id"] == hm_id for h in hms)

        finally:
            # Cleanup in reverse order
            if hm_id:
                try:
                    conoha_client.load_balancer.delete_health_monitor(hm_id)
                    if lb_id:
                        wait_for_lb_status(
                            conoha_client, lb_id, "ACTIVE", timeout=120
                        )
                except Exception:
                    pass

            if pool_id:
                try:
                    conoha_client.load_balancer.delete_pool(pool_id)
                    if lb_id:
                        wait_for_lb_status(
                            conoha_client, lb_id, "ACTIVE", timeout=120
                        )
                except Exception:
                    pass

            if listener_id:
                try:
                    conoha_client.load_balancer.delete_listener(listener_id)
                    if lb_id:
                        wait_for_lb_status(
                            conoha_client, lb_id, "ACTIVE", timeout=120
                        )
                except Exception:
                    pass

            if lb_id:
                try:
                    conoha_client.load_balancer.delete_load_balancer(lb_id)
                except Exception:
                    pass
