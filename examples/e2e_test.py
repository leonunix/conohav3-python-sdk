"""End-to-end test: create a VPS, manage lifecycle, and enable daily backup."""

import time

from conoha import ConoHaClient


def wait_for_status(get_func, target, timeout=300, interval=5):
    """Poll until resource reaches target status."""
    deadline = time.time() + timeout
    while True:
        resource = get_func()
        status = resource.get("status")
        print(f"  status: {status}")
        if status == target:
            return resource
        if status in ("ERROR", "error"):
            raise RuntimeError(f"Resource entered ERROR state: {resource}")
        if time.time() > deadline:
            raise TimeoutError(
                f"Timed out waiting for status '{target}' (last: '{status}')"
            )
        time.sleep(interval)


# ── Initialize client ────────────────────────────────────────
print("=== Initializing ConoHa client ===")
client = ConoHaClient(
    username="your-api-username",
    password="your-api-password",
    tenant_id="your-tenant-id",
)

# ── Find 1GB flavor ──────────────────────────────────────────
print("\n=== Finding 1GB flavor ===")
flavors = client.compute.list_flavors_detail()
flavor = next((f for f in flavors if f.get("name") == "g2l-t-c2m1"), None)
if not flavor:
    raise RuntimeError("1GB flavor (g2l-t-c2m1) not found")
flavor_id = flavor["id"]
print(f"Flavor: {flavor['name']} (id={flavor_id}, ram={flavor['ram']}MB)")

# ── Find Ubuntu 24.04 image ─────────────────────────────────
print("\n=== Finding Ubuntu 24.04 image ===")
images = client.image.list_images(visibility="public")
boot_image = next(
    (img for img in images if img.get("name") == "vmi-ubuntu-24.04-amd64"),
    None,
)
if not boot_image:
    raise RuntimeError("Image 'vmi-ubuntu-24.04-amd64' not found")
image_id = boot_image["id"]
print(f"Image: {boot_image['name']} (id={image_id})")

# ── Create 100GB boot volume ────────────────────────────────
print("\n=== Creating 100GB boot volume ===")
vol = client.volume.create_volume(
    size=100,
    name="sdk-test-daily-backup-boot",
    image_ref=image_id,
)
volume_id = vol["id"]
print(f"Volume created: {volume_id}")

print("Waiting for volume to become available...")
wait_for_status(
    lambda: client.volume.get_volume(volume_id),
    "available",
    timeout=180,
)
print("Volume is available.")

# ── Create server ────────────────────────────────────────────
print("\n=== Creating server (1GB plan) ===")
server = client.compute.create_server(
    flavor_id=flavor_id,
    admin_pass="SdkTest#2026",
    volume_id=volume_id,
    instance_name_tag="sdk-test-daily-backup",
)
server_id = server["id"]
print(f"Server created: {server_id}")

print("Waiting for server to become ACTIVE...")
server = wait_for_status(
    lambda: client.compute.get_server(server_id),
    "ACTIVE",
    timeout=300,
)
print(f"Server is ACTIVE.")

# ── Print server status ─────────────────────────────────────
print("\n=== Server details ===")
print(f"  ID:     {server['id']}")
print(f"  Name:   {server.get('metadata', {}).get('instance_name_tag')}")
print(f"  Status: {server['status']}")
print(f"  Flavor: {server.get('flavor', {}).get('id')}")

# ── Stop server ──────────────────────────────────────────────
print("\n=== Stopping server ===")
client.compute.stop_server(server_id)
print("Stop requested. Waiting for SHUTOFF...")
server = wait_for_status(
    lambda: client.compute.get_server(server_id),
    "SHUTOFF",
    timeout=180,
)
print("Server is SHUTOFF.")

# ── Start server ─────────────────────────────────────────────
print("\n=== Starting server ===")
client.compute.start_server(server_id)
print("Start requested. Waiting for ACTIVE...")
server = wait_for_status(
    lambda: client.compute.get_server(server_id),
    "ACTIVE",
    timeout=180,
)
print("Server is ACTIVE again.")

# ── Enable daily backup ──────────────────────────────────────
print("\n=== Enabling daily backup (retention=14) ===")
backup_result = client.volume.enable_auto_backup(
    server_id, schedule="daily", retention=14
)
print(f"Daily backup enabled: {backup_result}")

print("\n=== All steps completed successfully! ===")
print(f"Server ID: {server_id}")

# ── Cleanup prompt ──────────────────────────────────────────
print("\n" + "=" * 50)
print("WARNING: The server and volume are still running and incurring charges.")
print(f"  Server ID: {server_id}")
print(f"  Volume ID: {volume_id}")
reply = input("\nPress Enter to delete them, or type 'keep' to keep: ").strip()
if reply.lower() == "keep":
    print("Keeping resources. Remember to delete them manually later!")
else:
    print("Disabling auto-backup...")
    client.volume.disable_auto_backup(server_id)

    print("Deleting server...")
    client.compute.delete_server(server_id)
    print("Waiting for server to be deleted...")
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            s = client.compute.get_server(server_id)
            print(f"  status: {s['status']}")
            time.sleep(5)
        except Exception:
            print("Server deleted.")
            break

    print("Deleting volume...")
    try:
        client.volume.delete_volume(volume_id)
        print("Volume deleted.")
    except Exception as e:
        print(f"Could not delete volume (may already be gone): {e}")

    print("\nCleanup complete.")
