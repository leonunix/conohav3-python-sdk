"""Shared fixtures for integration tests.

Integration tests require real ConoHa API credentials set via
environment variables:
    CONOHA_USER_ID    - API user ID (UUID)
    CONOHA_PASSWORD   - API password
    CONOHA_TENANT_ID  - Tenant/Project ID
    CONOHA_REGION     - Region (default: c3j1)

Run integration tests with:
    source .env.test
    pytest tests/integration/ -v --run-integration
"""

import os
import time
import uuid

import pytest

from conoha import ConoHaClient
from conoha.exceptions import APIError, NotFoundError


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests against real ConoHa API",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="Need --run-integration to run")
        for item in items:
            if "integration" in str(item.fspath):
                item.add_marker(skip)


@pytest.fixture(scope="session")
def conoha_client():
    """Create a real ConoHa client for integration tests."""
    user_id = os.environ.get("CONOHA_USER_ID")
    password = os.environ.get("CONOHA_PASSWORD")
    tenant_id = os.environ.get("CONOHA_TENANT_ID")
    region = os.environ.get("CONOHA_REGION", "c3j1")

    if not all([user_id, password, tenant_id]):
        pytest.skip(
            "Integration tests require CONOHA_USER_ID, CONOHA_PASSWORD, "
            "and CONOHA_TENANT_ID environment variables"
        )

    client = ConoHaClient(
        user_id=user_id,
        password=password,
        tenant_id=tenant_id,
        region=region,
    )
    return client


def unique_name(prefix="sdk-inttest"):
    """Generate a unique resource name with random suffix."""
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}-{suffix}"


def wait_for_status(get_func, target_status, timeout=300, interval=5,
                    status_key="status"):
    """Poll a resource until it reaches a target status.

    Args:
        get_func: Callable that returns the resource dict.
        target_status: The desired status string (or list of statuses).
        timeout: Max seconds to wait.
        interval: Seconds between polls.
        status_key: Key in the resource dict to check.

    Returns:
        The resource dict once target status is reached.

    Raises:
        TimeoutError: If the target status is not reached within timeout.
    """
    if isinstance(target_status, str):
        target_status = [target_status]
    target_status_upper = [s.upper() for s in target_status]

    deadline = time.time() + timeout
    while True:
        resource = get_func()
        current = resource.get(status_key, "").upper()
        if current in target_status_upper:
            return resource
        if current in ("ERROR", "FAILED"):
            raise RuntimeError(
                f"Resource entered {current} state instead of "
                f"{target_status}: {resource}"
            )
        if time.time() > deadline:
            raise TimeoutError(
                f"Timed out waiting for status {target_status}, "
                f"current: {current}"
            )
        time.sleep(interval)


def wait_for_lb_status(client, lb_id, target_status="ACTIVE",
                       status_key="provisioning_status",
                       timeout=300, interval=5):
    """Wait for a load balancer to reach a provisioning status."""
    return wait_for_status(
        get_func=lambda: client.load_balancer.get_load_balancer(lb_id),
        target_status=target_status,
        timeout=timeout,
        interval=interval,
        status_key=status_key,
    )


def wait_for_deleted(get_func, timeout=120, interval=5):
    """Poll until a resource returns 404 (deleted).

    Args:
        get_func: Callable that fetches the resource.
        timeout: Max seconds to wait.
        interval: Seconds between polls.

    Raises:
        TimeoutError: If the resource is still found after timeout.
    """
    deadline = time.time() + timeout
    while True:
        try:
            get_func()
        except NotFoundError:
            return
        except APIError:
            return
        if time.time() > deadline:
            raise TimeoutError("Timed out waiting for resource deletion")
        time.sleep(interval)
