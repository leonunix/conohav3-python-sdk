# ConoHa Python SDK

A Python SDK for the [ConoHa VPS v3 API](https://doc.conoha.jp/reference/api-vps3/).

[日本語版 README はこちら](README.ja.md)

## Features

- Full coverage of ConoHa VPS v3 API (8 services, 100+ endpoints)
- Automatic token authentication and refresh
- Service catalog auto-discovery from token response
- Lazy-loaded service clients
- Typed exception hierarchy for error handling

## Supported Services

| Service | Description |
|---------|-------------|
| **Identity** | Credential management |
| **Compute** | Servers, flavors, keypairs, monitoring graphs |
| **Volume** | Block storage volumes, types, backups |
| **Image** | VM images, ISO images, quota management |
| **Network** | Security groups/rules, networks, subnets, ports |
| **Load Balancer** | Load balancers, listeners, pools, members, health monitors |
| **DNS** | Domains and DNS records |
| **Object Storage** | Containers and objects |

## Installation

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

## Quick Start

```python
from conoha import ConoHaClient

client = ConoHaClient(
    username="your-api-username",
    password="your-api-password",
    tenant_id="your-tenant-id",
)

# List servers
servers = client.compute.list_servers_detail()
for server in servers["servers"]:
    print(f"{server['id']}: {server['status']}")
```

## Usage

### Authentication

The client authenticates automatically on first API call. You can also authenticate explicitly:

```python
client = ConoHaClient(
    username="gncu12345678",
    password="your-password",
    tenant_id="0123456789abcdef",
)

# Explicit authentication (optional - happens automatically)
client.authenticate()
```

You can also pass a pre-existing token:

```python
client = ConoHaClient(
    token="your-existing-token",
    tenant_id="your-tenant-id",
)
```

### Compute

```python
# List servers
servers = client.compute.list_servers()

# Create a server
server = client.compute.create_server(
    flavor_id="flavor-uuid",
    admin_pass="secure-password",
    volume_id="boot-volume-uuid",
    instance_name_tag="my-server",
    key_name="my-keypair",
    security_groups=[{"name": "default"}],
)

# Server actions
client.compute.start_server("server-id")
client.compute.stop_server("server-id")
client.compute.reboot_server("server-id")

# Resize (change plan)
client.compute.resize_server("server-id", "new-flavor-id")
client.compute.confirm_resize("server-id")

# Get console URL
console = client.compute.get_console_url("server-id", console_type="novnc")
print(console["remote_console"]["url"])

# SSH keypairs
keypairs = client.compute.list_keypairs()
new_key = client.compute.create_keypair("my-key")
print(new_key["keypair"]["private_key"])

# Monitoring
cpu_data = client.compute.get_cpu_graph("server-id")
```

### Volume (Block Storage)

```python
# List volumes
volumes = client.volume.list_volumes_detail()

# Create a volume
volume = client.volume.create_volume(size=100, name="data-vol")

# Save volume as image
client.volume.save_volume_as_image("volume-id", "my-image-name")

# Backups
backups = client.volume.list_backups_detail()
client.volume.enable_auto_backup("server-id")
```

### Image

```python
# List images
images = client.image.list_images(visibility="private")

# Upload ISO image
iso = client.image.create_iso_image("my-distro.iso")
with open("my-distro.iso", "rb") as f:
    client.image.upload_iso_image(iso["id"], f)

# Quota management
usage = client.image.get_image_usage()
client.image.update_image_quota(550)  # 550GB
```

### Network

```python
# Security groups
groups = client.network.list_security_groups()
new_sg = client.network.create_security_group("web-server")

# Add rule: allow HTTP ingress
client.network.create_security_group_rule(
    security_group_id=new_sg["security_group"]["id"],
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=80,
    port_range_max=80,
)

# Local networks
network = client.network.create_network()
subnet = client.network.create_subnet(
    network_id=network["network"]["id"],
    cidr="10.0.0.0/24",
)

# Additional IP allocation
port = client.network.create_additional_ip_port(count=1)
```

### Load Balancer

```python
# Create a load balancer
lb = client.load_balancer.create_load_balancer(
    name="my-lb",
    vip_subnet_id="subnet-id",
)

# Create listener
listener = client.load_balancer.create_listener(
    loadbalancer_id=lb["loadbalancer"]["id"],
    protocol="TCP",
    protocol_port=80,
    name="http-listener",
)

# Create pool
pool = client.load_balancer.create_pool(
    listener_id=listener["listener"]["id"],
    protocol="TCP",
    lb_algorithm="ROUND_ROBIN",
    name="web-pool",
)

# Add members
client.load_balancer.create_member(
    pool_id=pool["pool"]["id"],
    address="203.0.113.10",
    protocol_port=80,
)

# Health monitor
client.load_balancer.create_health_monitor(
    pool_id=pool["pool"]["id"],
    monitor_type="TCP",
    delay=30,
    timeout=10,
    max_retries=3,
)
```

### DNS

```python
# Register a domain
domain = client.dns.create_domain(
    name="example.com.",
    ttl=3600,
    email="admin@example.com",
)

# Add records
client.dns.create_record(
    domain_id=domain["uuid"],
    name="www.example.com.",
    record_type="A",
    data="203.0.113.10",
)

client.dns.create_record(
    domain_id=domain["uuid"],
    name="example.com.",
    record_type="MX",
    data="mail.example.com.",
    priority=10,
)
```

### Object Storage

```python
# Set quota (minimum 100GB)
client.object_storage.set_account_quota(100)

# Containers
client.object_storage.create_container("my-bucket")
containers = client.object_storage.list_containers()

# Upload / download objects
client.object_storage.upload_object(
    "my-bucket", "hello.txt", b"Hello, World!"
)
resp = client.object_storage.download_object("my-bucket", "hello.txt")
print(resp.content)

# Delete
client.object_storage.delete_object("my-bucket", "hello.txt")
client.object_storage.delete_container("my-bucket")
```

## Error Handling

```python
from conoha.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    ConflictError,
    TokenExpiredError,
)

try:
    server = client.compute.get_server("nonexistent-id")
except NotFoundError:
    print("Server not found")
except AuthenticationError:
    print("Invalid credentials")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `region` | `c3j1` | ConoHa region code |
| `timeout` | `30` | HTTP request timeout (seconds) |

Tokens are valid for 24 hours and automatically refreshed when expired.

## Development

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Unit tests with coverage
pytest tests/unit/ --cov=conoha --cov-report=term-missing

# Integration tests (requires real credentials)
CONOHA_USERNAME=xxx CONOHA_PASSWORD=xxx CONOHA_TENANT_ID=xxx \
  pytest tests/integration/ --run-integration
```

## Project Structure

```
conoha-python-sdk/
├── conoha/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Main client with auth and service discovery
│   ├── config.py            # Constants and base URLs
│   ├── exceptions.py        # Exception hierarchy
│   ├── base.py              # Base service class with HTTP helpers
│   ├── identity.py          # Identity API (credentials)
│   ├── compute.py           # Compute API (servers, flavors, keypairs)
│   ├── volume.py            # Block Storage API (volumes, backups)
│   ├── image.py             # Image API (images, ISO, quota)
│   ├── network.py           # Network API (SGs, networks, ports)
│   ├── loadbalancer.py      # Load Balancer API
│   ├── dns.py               # DNS API (domains, records)
│   └── object_storage.py    # Object Storage API
├── tests/
│   ├── unit/                # Unit tests (103 tests)
│   └── integration/         # Integration tests
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## License

MIT
