"""Integration tests for Compute API."""

import time

import pytest

from conoha.exceptions import NotFoundError
from tests.integration.conftest import (
    unique_name,
    wait_for_status,
    wait_for_deleted,
)


class TestComputeFlavors:
    def test_list_flavors(self, conoha_client):
        """List all available flavors."""
        flavors = conoha_client.compute.list_flavors()
        assert isinstance(flavors, list)
        assert len(flavors) > 0

    def test_list_flavors_detail(self, conoha_client):
        """List flavors with full details."""
        flavors = conoha_client.compute.list_flavors_detail()
        assert isinstance(flavors, list)
        assert len(flavors) > 0
        assert "vcpus" in flavors[0] or "ram" in flavors[0]

    def test_get_flavor(self, conoha_client):
        """Get details for the first available flavor."""
        flavors = conoha_client.compute.list_flavors()
        assert len(flavors) > 0
        flavor = conoha_client.compute.get_flavor(flavors[0]["id"])
        assert "id" in flavor
        assert "name" in flavor


class TestComputeKeypairs:
    def test_keypair_crud(self, conoha_client):
        """Full keypair lifecycle: create → get → list → delete."""
        name = unique_name("sdk-inttest-kp")
        kp = None

        try:
            # Create (auto-generate)
            kp = conoha_client.compute.create_keypair(name)
            assert kp["name"] == name
            assert "public_key" in kp
            assert "private_key" in kp  # Only returned on create

            # Get
            fetched = conoha_client.compute.get_keypair(name)
            assert fetched["name"] == name
            assert "public_key" in fetched

            # List
            keypairs = conoha_client.compute.list_keypairs()
            names = [k["keypair"]["name"] for k in keypairs]
            assert name in names

        finally:
            # Delete
            if kp:
                conoha_client.compute.delete_keypair(name)

        # Verify deleted
        with pytest.raises(NotFoundError):
            conoha_client.compute.get_keypair(name)


class TestComputeServerLifecycle:
    """Full server lifecycle test.

    Creates a boot volume → server, then tests all server operations
    and cleans up by deleting both server and volume.
    """

    def test_server_lifecycle(self, conoha_client):
        """Create server, perform operations, then delete."""
        server_id = None
        volume_id = None
        extra_volume_id = None
        server_name = unique_name("sdk-inttest-srv")

        try:
            # Find the g2l-t-c2m1 flavor
            flavors = conoha_client.compute.list_flavors_detail()
            flavor = next(
                (f for f in flavors if f.get("name") == "g2l-t-c2m1"),
                flavors[0],
            )
            flavor_id = flavor["id"]

            # Get a public image for boot volume
            images = conoha_client.image.list_images(visibility="public")
            # Pick a small Linux image
            boot_image = None
            for img in images:
                name_lower = (img.get("name") or "").lower()
                if "ubuntu" in name_lower or "centos" in name_lower or "alma" in name_lower:
                    boot_image = img
                    break
            if not boot_image:
                boot_image = images[0]
            image_id = boot_image["id"]

            # Create boot volume from image
            vol = conoha_client.volume.create_volume(
                size=30,
                name=unique_name("sdk-inttest-vol"),
                image_ref=image_id,
            )
            volume_id = vol["id"]
            assert volume_id is not None

            # Wait for volume to become available
            wait_for_status(
                lambda: conoha_client.volume.get_volume(volume_id),
                "available",
                timeout=120,
            )

            # Create server
            server = conoha_client.compute.create_server(
                flavor_id=flavor_id,
                admin_pass="TestP@ss1234",
                volume_id=volume_id,
                instance_name_tag=server_name,
            )
            server_id = server["id"]
            assert server_id is not None

            # Wait for ACTIVE
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "ACTIVE",
                timeout=300,
            )

            # Get server detail
            srv = conoha_client.compute.get_server(server_id)
            assert srv["id"] == server_id
            assert srv["status"] == "ACTIVE"

            # List servers (should contain ours)
            servers = conoha_client.compute.list_servers()
            assert any(s["id"] == server_id for s in servers)

            # List servers detail
            servers_detail = conoha_client.compute.list_servers_detail()
            srv_detail = next(
                (s for s in servers_detail if s["id"] == server_id), None
            )
            assert srv_detail is not None
            assert "status" in srv_detail

            # Get addresses
            addresses = conoha_client.compute.get_server_addresses(server_id)
            assert isinstance(addresses, dict)

            # Get security groups
            sgs = conoha_client.compute.get_server_security_groups(server_id)
            assert isinstance(sgs, list)

            # Get metadata
            meta = conoha_client.compute.get_server_metadata(server_id)
            assert isinstance(meta, dict)
            assert meta.get("instance_name_tag") == server_name

            # Update metadata
            updated_meta = conoha_client.compute.update_server_metadata(
                server_id, {"instance_name_tag": server_name + "-updated"}
            )
            assert updated_meta["instance_name_tag"] == server_name + "-updated"

            # Get VNC console
            console = conoha_client.compute.get_console_url(server_id)
            assert "url" in console

            # List attached ports
            ports = conoha_client.compute.list_attached_ports(server_id)
            assert isinstance(ports, list)

            # List attached volumes
            vols = conoha_client.compute.list_attached_volumes(server_id)
            assert isinstance(vols, list)

            # Get attached volume detail (boot volume)
            if vols:
                att_vol_id = vols[0].get("volumeId", vols[0].get("id"))
                vol_attachment = conoha_client.compute.get_attached_volume(
                    server_id, att_vol_id
                )
                assert isinstance(vol_attachment, dict)

            # Get addresses by network name
            addresses = conoha_client.compute.get_server_addresses(server_id)
            if addresses:
                # Pick the first network name
                network_name = list(addresses.keys())[0]
                net_addrs = conoha_client.compute.get_server_addresses_by_network(
                    server_id, network_name
                )
                assert isinstance(net_addrs, list)
                if net_addrs:
                    assert "addr" in net_addrs[0]

            # Set server settings (hw_video_model)
            try:
                conoha_client.compute.set_server_settings(
                    server_id, hw_video_model="vga"
                )
            except Exception:
                # Some plans/images may not support this action
                pass

            # --- Monitoring graphs ---
            cpu_data = conoha_client.compute.get_cpu_graph(server_id)
            assert cpu_data is not None

            disk_data = conoha_client.compute.get_disk_io_graph(server_id)
            assert disk_data is not None

            if ports:
                traffic_data = conoha_client.compute.get_traffic_graph(
                    server_id, ports[0]["port_id"]
                )
                assert traffic_data is not None

            # Stop server
            conoha_client.compute.stop_server(server_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "SHUTOFF",
                timeout=120,
            )

            # Start server
            conoha_client.compute.start_server(server_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "ACTIVE",
                timeout=120,
            )

            # Reboot server
            conoha_client.compute.reboot_server(server_id)
            # Brief wait then check it comes back to ACTIVE
            time.sleep(5)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "ACTIVE",
                timeout=300,
            )

            # --- Plan change (resize) from c2m1 → c3m2 ---
            # Find the c3m2 flavor
            target_flavor = next(
                (f for f in flavors if f.get("name") == "g2l-t-c3m2"),
                None,
            )
            assert target_flavor is not None, "g2l-t-c3m2 flavor not found"
            target_flavor_id = target_flavor["id"]

            # Force stop server before resize
            conoha_client.compute.force_stop_server(server_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "SHUTOFF",
                timeout=120,
            )

            # --- Attach / get / detach extra volume (server is stopped) ---
            extra_vol = conoha_client.volume.create_volume(
                size=30,
                name=unique_name("sdk-inttest-xvol"),
            )
            extra_volume_id = extra_vol["id"]
            wait_for_status(
                lambda: conoha_client.volume.get_volume(extra_volume_id),
                "available",
                timeout=120,
            )

            # Attach
            attachment = conoha_client.compute.attach_volume(
                server_id, extra_volume_id
            )
            assert attachment["volumeId"] == extra_volume_id
            time.sleep(5)

            # Get attached volume detail
            att_detail = conoha_client.compute.get_attached_volume(
                server_id, extra_volume_id
            )
            assert att_detail["volumeId"] == extra_volume_id

            # Detach
            conoha_client.compute.detach_volume(server_id, extra_volume_id)
            wait_for_status(
                lambda: conoha_client.volume.get_volume(extra_volume_id),
                "available",
                timeout=120,
            )

            # Clean up extra volume
            conoha_client.volume.delete_volume(extra_volume_id)
            extra_volume_id = None

            # Resize server
            conoha_client.compute.resize_server(server_id, target_flavor_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "VERIFY_RESIZE",
                timeout=300,
            )

            # Confirm resize
            conoha_client.compute.confirm_resize(server_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                ["ACTIVE", "SHUTOFF"],
                timeout=300,
            )

            # Verify flavor changed
            srv = conoha_client.compute.get_server(server_id)
            assert srv["flavor"]["id"] == target_flavor_id

            # --- Revert resize: resize to c2m1, then revert back to c3m2 ---
            # Ensure server is stopped
            if srv["status"] != "SHUTOFF":
                conoha_client.compute.stop_server(server_id)
                wait_for_status(
                    lambda: conoha_client.compute.get_server(server_id),
                    "SHUTOFF",
                    timeout=120,
                )

            # Resize to original c2m1
            conoha_client.compute.resize_server(server_id, flavor_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                "VERIFY_RESIZE",
                timeout=300,
            )

            # Revert (should go back to c3m2)
            conoha_client.compute.revert_resize(server_id)
            wait_for_status(
                lambda: conoha_client.compute.get_server(server_id),
                ["ACTIVE", "SHUTOFF"],
                timeout=300,
            )

            # Verify flavor reverted to c3m2
            srv = conoha_client.compute.get_server(server_id)
            assert srv["flavor"]["id"] == target_flavor_id

        finally:
            # Cleanup: delete server
            if server_id:
                try:
                    # Wait for server to leave transitional states
                    # (REBOOT, BUILD, RESIZE, etc.) before deleting
                    wait_for_status(
                        lambda: conoha_client.compute.get_server(server_id),
                        ["ACTIVE", "SHUTOFF", "VERIFY_RESIZE", "ERROR"],
                        timeout=300,
                    )
                except Exception:
                    pass
                try:
                    conoha_client.compute.delete_server(server_id)
                    wait_for_deleted(
                        lambda: conoha_client.compute.get_server(server_id),
                        timeout=120,
                    )
                except Exception:
                    pass

            # Cleanup: delete extra volume
            if extra_volume_id:
                try:
                    wait_for_status(
                        lambda: conoha_client.volume.get_volume(extra_volume_id),
                        ["available", "error"],
                        timeout=120,
                    )
                    conoha_client.volume.delete_volume(extra_volume_id)
                except Exception:
                    pass

            # Cleanup: delete volume
            if volume_id:
                # Wait for volume to detach
                time.sleep(10)
                try:
                    wait_for_status(
                        lambda: conoha_client.volume.get_volume(volume_id),
                        ["available", "error"],
                        timeout=120,
                    )
                    conoha_client.volume.delete_volume(volume_id)
                except Exception:
                    pass
