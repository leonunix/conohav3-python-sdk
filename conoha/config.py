"""ConoHa SDK configuration."""

# Default region
DEFAULT_REGION = "c3j1"

# Base URL templates (region is substituted)
BASE_URLS = {
    "identity": "https://identity.{region}.conoha.io",
    "compute": "https://compute.{region}.conoha.io",
    "block_storage": "https://block-storage.{region}.conoha.io",
    "image": "https://image-service.{region}.conoha.io",
    "network": "https://networking.{region}.conoha.io",
    "load_balancer": "https://lbaas.{region}.conoha.io",
    "dns": "https://dns-service.{region}.conoha.io",
    "object_storage": "https://object-storage.{region}.conoha.io",
}

# Environment variable names for endpoint overrides
# e.g. CONOHA_ENDPOINT_COMPUTE=https://compute.c3j1.conoha.io
ENDPOINT_ENV_PREFIX = "CONOHA_ENDPOINT_"
ENDPOINT_ENV_MAP = {
    "CONOHA_ENDPOINT_IDENTITY": "identity",
    "CONOHA_ENDPOINT_COMPUTE": "compute",
    "CONOHA_ENDPOINT_BLOCK_STORAGE": "block_storage",
    "CONOHA_ENDPOINT_IMAGE": "image",
    "CONOHA_ENDPOINT_NETWORK": "network",
    "CONOHA_ENDPOINT_LOAD_BALANCER": "load_balancer",
    "CONOHA_ENDPOINT_DNS": "dns",
    "CONOHA_ENDPOINT_OBJECT_STORAGE": "object_storage",
}

# Token validity period in seconds (24 hours)
TOKEN_VALIDITY = 86400

# Default timeout for API requests in seconds
DEFAULT_TIMEOUT = 30
