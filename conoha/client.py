"""ConoHa VPS v3 API client."""

import os
import time
from datetime import datetime, timezone

import requests

from .config import BASE_URLS, DEFAULT_REGION, DEFAULT_TIMEOUT, ENDPOINT_ENV_MAP
from .exceptions import AuthenticationError
from .identity import IdentityService
from .compute import ComputeService
from .volume import VolumeService
from .image import ImageService
from .network import NetworkService
from .loadbalancer import LoadBalancerService
from .dns import DNSService
from .object_storage import ObjectStorageService


class ConoHaClient:
    """Main client for interacting with the ConoHa VPS v3 API.

    Usage:
        client = ConoHaClient(
            username="api_user",
            password="api_password",
            tenant_id="your_tenant_id",
        )
        servers = client.compute.list_servers()

    All service modules are available as properties:
        - client.identity
        - client.compute
        - client.volume
        - client.image
        - client.network
        - client.load_balancer
        - client.dns
        - client.object_storage
    """

    def __init__(
        self,
        username=None,
        password=None,
        tenant_id=None,
        user_id=None,
        tenant_name=None,
        region=DEFAULT_REGION,
        token=None,
        timeout=DEFAULT_TIMEOUT,
        endpoints=None,
    ):
        self.region = region
        self.timeout = timeout
        self._token = token
        self._token_expires_at = None
        self._tenant_id = tenant_id
        self._user_id = user_id

        # Auth credentials
        self._username = username
        self._password = password
        self._tenant_name = tenant_name

        # Service endpoints resolution order:
        #   1. User-specified via `endpoints` parameter (highest priority)
        #   2. Environment variables (CONOHA_ENDPOINT_COMPUTE, etc.)
        #   3. Service catalog from authentication response
        #   4. Template URLs from config.py (lowest priority)
        self._user_endpoints = dict(endpoints) if endpoints else {}
        self._env_endpoints = self._load_env_endpoints()
        self._catalog_endpoints = {}

        # Initialize service modules (lazy — they call _get_endpoint)
        self._identity = None
        self._compute = None
        self._volume = None
        self._image = None
        self._network = None
        self._load_balancer = None
        self._dns = None
        self._object_storage = None

        # Auto-authenticate if credentials provided
        if not token and (username or user_id) and password:
            self.authenticate()

    @property
    def token(self):
        """Get the current authentication token, refreshing if expired."""
        if self._token and not self._is_token_expired():
            return self._token
        if (self._username or self._user_id) and self._password:
            self.authenticate()
            return self._token
        raise AuthenticationError("No valid token. Call authenticate() first.")

    @property
    def tenant_id(self):
        return self._tenant_id

    @property
    def user_id(self):
        return self._user_id

    def _is_token_expired(self):
        if self._token_expires_at is None:
            return False
        return time.time() >= self._token_expires_at

    @staticmethod
    def _load_env_endpoints():
        """Load endpoint overrides from environment variables."""
        endpoints = {}
        for env_var, service_name in ENDPOINT_ENV_MAP.items():
            value = os.environ.get(env_var)
            if value:
                endpoints[service_name] = value.rstrip("/")
        return endpoints

    def _get_endpoint(self, service_name):
        """Get the base URL for a service.

        Resolution order:
            1. User-specified via constructor `endpoints` param
            2. Environment variable (CONOHA_ENDPOINT_XXX)
            3. Service catalog from auth response
            4. Template URL from config.py
        """
        # 1. User-specified
        if service_name in self._user_endpoints:
            return self._user_endpoints[service_name]
        # 2. Environment variable
        if service_name in self._env_endpoints:
            return self._env_endpoints[service_name]
        # 3. Service catalog
        if service_name in self._catalog_endpoints:
            return self._catalog_endpoints[service_name]
        # 4. Template fallback
        template = BASE_URLS.get(service_name)
        if template:
            return template.format(region=self.region)
        raise ValueError(f"Unknown service: {service_name}")

    def authenticate(self):
        """Authenticate with the ConoHa Identity API and obtain a token.

        POST /v3/auth/tokens
        """
        identity_url = self._get_endpoint("identity")
        url = f"{identity_url}/v3/auth/tokens"

        # Build auth body
        if self._user_id:
            user_block = {
                "id": self._user_id,
                "password": self._password,
            }
        else:
            user_block = {
                "name": self._username,
                "password": self._password,
            }

        if self._tenant_id:
            scope_block = {"project": {"id": self._tenant_id}}
        elif self._tenant_name:
            scope_block = {"project": {"name": self._tenant_name}}
        else:
            scope_block = None

        body = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {"user": user_block},
                },
            }
        }
        if scope_block:
            body["auth"]["scope"] = scope_block

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, json=body, headers=headers,
                             timeout=self.timeout)

        if resp.status_code != 201:
            raise AuthenticationError(
                f"Authentication failed: {resp.status_code} {resp.text}"
            )

        self._token = resp.headers.get("x-subject-token")
        data = resp.json()["token"]

        # Set expiry from response, with 5-minute safety buffer
        expires_at_str = data.get("expires_at")
        if expires_at_str:
            expires_dt = datetime.fromisoformat(
                expires_at_str.replace("Z", "+00:00")
            )
            self._token_expires_at = expires_dt.timestamp() - 300
        else:
            self._token_expires_at = time.time() + 86400 - 300

        # Extract user and project info
        if "project" in data:
            self._tenant_id = data["project"]["id"]
        if "user" in data:
            self._user_id = data["user"]["id"]

        # Parse service catalog for endpoints
        self._parse_catalog(data.get("catalog", []))

        return self._token

    def _parse_catalog(self, catalog):
        """Parse the service catalog from token response."""
        service_map = {
            "identity": "identity",
            "compute": "compute",
            "volumev3": "block_storage",
            "image": "image",
            "network": "network",
            "load-balancer": "load_balancer",
            "dns": "dns",
            "object-store": "object_storage",
        }
        for entry in catalog:
            service_type = entry.get("type", "")
            sdk_name = service_map.get(service_type)
            if sdk_name:
                for endpoint in entry.get("endpoints", []):
                    if endpoint.get("interface") == "public":
                        self._catalog_endpoints[sdk_name] = endpoint["url"]
                        break

    # ── Service Properties ───────────────────────────────────────

    @property
    def identity(self):
        if self._identity is None:
            self._identity = IdentityService(self)
        return self._identity

    @property
    def compute(self):
        if self._compute is None:
            self._compute = ComputeService(self)
        return self._compute

    @property
    def volume(self):
        if self._volume is None:
            self._volume = VolumeService(self)
        return self._volume

    @property
    def image(self):
        if self._image is None:
            self._image = ImageService(self)
        return self._image

    @property
    def network(self):
        if self._network is None:
            self._network = NetworkService(self)
        return self._network

    @property
    def load_balancer(self):
        if self._load_balancer is None:
            self._load_balancer = LoadBalancerService(self)
        return self._load_balancer

    @property
    def dns(self):
        if self._dns is None:
            self._dns = DNSService(self)
        return self._dns

    @property
    def object_storage(self):
        if self._object_storage is None:
            self._object_storage = ObjectStorageService(self)
        return self._object_storage
