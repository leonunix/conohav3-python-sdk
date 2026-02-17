"""ConoHa Compute API service."""

from .base import BaseService


class ComputeService(BaseService):
    """Compute API: server management, flavors, keypairs, monitoring.

    Base URL: https://compute.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("compute")

    # ── Servers ──────────────────────────────────────────────────

    def list_servers(self):
        """List servers (minimal info).

        GET /v2.1/servers
        """
        url = f"{self._base_url}/v2.1/servers"
        resp = self._get(url)
        return resp.json()["servers"]

    def list_servers_detail(self):
        """List servers with full details.

        GET /v2.1/servers/detail
        """
        url = f"{self._base_url}/v2.1/servers/detail"
        resp = self._get(url)
        return resp.json()["servers"]

    def get_server(self, server_id):
        """Get server details.

        GET /v2.1/servers/{server_id}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}"
        resp = self._get(url)
        return resp.json()["server"]

    def create_server(
        self,
        flavor_id,
        admin_pass,
        volume_id,
        instance_name_tag,
        key_name=None,
        user_data=None,
        security_groups=None,
    ):
        """Create a new server.

        POST /v2.1/servers
        """
        body = {
            "server": {
                "flavorRef": flavor_id,
                "adminPass": admin_pass,
                "block_device_mapping_v2": [{"uuid": volume_id}],
                "metadata": {"instance_name_tag": instance_name_tag},
            }
        }
        if key_name:
            body["server"]["key_name"] = key_name
        if user_data:
            body["server"]["user_data"] = user_data
        if security_groups:
            body["server"]["security_groups"] = security_groups

        url = f"{self._base_url}/v2.1/servers"
        resp = self._post(url, json=body)
        return resp.json()["server"]

    def delete_server(self, server_id):
        """Delete a server.

        DELETE /v2.1/servers/{server_id}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}"
        self._delete(url)

    # ── Server Actions ───────────────────────────────────────────

    def _server_action(self, server_id, action_body):
        url = f"{self._base_url}/v2.1/servers/{server_id}/action"
        return self._post(url, json=action_body)

    def start_server(self, server_id):
        """Start a server.

        POST /v2.1/servers/{server_id}/action {"os-start": null}
        """
        self._server_action(server_id, {"os-start": None})

    def stop_server(self, server_id):
        """Stop a server.

        POST /v2.1/servers/{server_id}/action {"os-stop": null}
        """
        self._server_action(server_id, {"os-stop": None})

    def reboot_server(self, server_id, reboot_type="SOFT"):
        """Reboot a server.

        POST /v2.1/servers/{server_id}/action {"reboot": {"type": "SOFT"}}
        """
        self._server_action(server_id, {"reboot": {"type": reboot_type}})

    def force_stop_server(self, server_id):
        """Force stop a server.

        POST /v2.1/servers/{server_id}/action {"os-stop": {"force_shutdown": true}}
        """
        self._server_action(
            server_id, {"os-stop": {"force_shutdown": True}}
        )

    def resize_server(self, server_id, flavor_id):
        """Resize a server (change plan). Server must be stopped.

        POST /v2.1/servers/{server_id}/action {"resize": {"flavorRef": ...}}
        """
        self._server_action(server_id, {"resize": {"flavorRef": flavor_id}})

    def confirm_resize(self, server_id):
        """Confirm a server resize.

        POST /v2.1/servers/{server_id}/action {"confirmResize": null}
        """
        self._server_action(server_id, {"confirmResize": None})

    def revert_resize(self, server_id):
        """Revert a server resize.

        POST /v2.1/servers/{server_id}/action {"revertResize": null}
        """
        self._server_action(server_id, {"revertResize": None})

    def rebuild_server(self, server_id, image_id, admin_pass):
        """Rebuild (reinstall OS) a server.

        POST /v2.1/servers/{server_id}/action
        """
        self._server_action(
            server_id,
            {"rebuild": {"imageRef": image_id, "adminPass": admin_pass}},
        )

    def mount_iso(self, server_id, image_id):
        """Mount an ISO image on a server.

        POST /v2.1/servers/{server_id}/action {"mountImage": ...}
        """
        self._server_action(
            server_id, {"mountImage": {"imageid": image_id}}
        )

    def unmount_iso(self, server_id, image_id):
        """Unmount an ISO image from a server.

        POST /v2.1/servers/{server_id}/action {"unmountImage": ...}
        """
        self._server_action(
            server_id, {"unmountImage": {"imageid": image_id}}
        )

    # ── Server Metadata ──────────────────────────────────────────

    def get_server_metadata(self, server_id):
        """Get server metadata.

        GET /v2.1/servers/{server_id}/metadata
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/metadata"
        resp = self._get(url)
        return resp.json()["metadata"]

    def update_server_metadata(self, server_id, metadata):
        """Update server metadata.

        PUT /v2.1/servers/{server_id}/metadata
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/metadata"
        resp = self._put(url, json={"metadata": metadata})
        return resp.json()["metadata"]

    # ── Server Addresses ─────────────────────────────────────────

    def get_server_addresses(self, server_id):
        """Get server IP addresses.

        GET /v2.1/servers/{server_id}/ips
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/ips"
        resp = self._get(url)
        return resp.json()["addresses"]

    def get_server_addresses_by_network(self, server_id, network_name):
        """Get server IP addresses for a specific network.

        GET /v2.1/servers/{server_id}/ips/{network_name}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/ips/{network_name}"
        resp = self._get(url)
        return resp.json()[network_name]

    # ── Server Settings ──────────────────────────────────────

    def set_server_settings(self, server_id, hw_video_model=None,
                            hw_vif_model=None, hw_disk_bus=None):
        """Update server hardware settings. Server must be stopped.

        POST /v2.1/servers/{server_id}/action
        """
        settings = {}
        if hw_video_model is not None:
            settings["hwVideoModel"] = hw_video_model
        if hw_vif_model is not None:
            settings["hwVifModel"] = hw_vif_model
        if hw_disk_bus is not None:
            settings["hwDiskBus"] = hw_disk_bus
        self._server_action(server_id, {"setServerSettings": settings})

    # ── Server Security Groups ───────────────────────────────────

    def get_server_security_groups(self, server_id):
        """Get security groups attached to a server.

        GET /v2.1/servers/{server_id}/os-security-groups
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-security-groups"
        resp = self._get(url)
        return resp.json()["security_groups"]

    # ── Console ──────────────────────────────────────────────────

    def get_console_url(self, server_id, console_type="novnc"):
        """Get remote console URL.

        POST /v2.1/servers/{server_id}/remote-consoles
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/remote-consoles"
        body = {
            "remote_console": {"protocol": "vnc", "type": console_type}
        }
        resp = self._post(url, json=body)
        return resp.json()["remote_console"]

    # ── Flavors ──────────────────────────────────────────────────

    def list_flavors(self):
        """List flavors (minimal info).

        GET /v2.1/flavors
        """
        url = f"{self._base_url}/v2.1/flavors"
        resp = self._get(url)
        return resp.json()["flavors"]

    def list_flavors_detail(self):
        """List flavors with full details.

        GET /v2.1/flavors/detail
        """
        url = f"{self._base_url}/v2.1/flavors/detail"
        resp = self._get(url)
        return resp.json()["flavors"]

    def get_flavor(self, flavor_id):
        """Get flavor details.

        GET /v2.1/flavors/{flavor_id}
        """
        url = f"{self._base_url}/v2.1/flavors/{flavor_id}"
        resp = self._get(url)
        return resp.json()["flavor"]

    # ── SSH Keypairs ─────────────────────────────────────────────

    def list_keypairs(self):
        """List SSH keypairs.

        GET /v2.1/os-keypairs
        """
        url = f"{self._base_url}/v2.1/os-keypairs"
        resp = self._get(url)
        return resp.json()["keypairs"]

    def create_keypair(self, name, public_key=None):
        """Create an SSH keypair.

        POST /v2.1/os-keypairs
        If public_key is not provided, a new keypair is generated.
        """
        body = {"keypair": {"name": name}}
        if public_key:
            body["keypair"]["public_key"] = public_key
        url = f"{self._base_url}/v2.1/os-keypairs"
        resp = self._post(url, json=body)
        return resp.json()["keypair"]

    def get_keypair(self, name):
        """Get keypair details.

        GET /v2.1/os-keypairs/{name}
        """
        url = f"{self._base_url}/v2.1/os-keypairs/{name}"
        resp = self._get(url)
        return resp.json()["keypair"]

    def delete_keypair(self, name):
        """Delete an SSH keypair.

        DELETE /v2.1/os-keypairs/{name}
        """
        url = f"{self._base_url}/v2.1/os-keypairs/{name}"
        self._delete(url)

    # ── Attached Ports ───────────────────────────────────────────

    def list_attached_ports(self, server_id):
        """List ports attached to a server.

        GET /v2.1/servers/{server_id}/os-interface
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-interface"
        resp = self._get(url)
        return resp.json()["interfaceAttachments"]

    def get_attached_port(self, server_id, port_id):
        """Get details of an attached port.

        GET /v2.1/servers/{server_id}/os-interface/{port_id}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-interface/{port_id}"
        resp = self._get(url)
        return resp.json()["interfaceAttachment"]

    def attach_port(self, server_id, port_id):
        """Attach a port to a server.

        POST /v2.1/servers/{server_id}/os-interface
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-interface"
        resp = self._post(
            url, json={"interfaceAttachment": {"port_id": port_id}}
        )
        return resp.json()["interfaceAttachment"]

    def detach_port(self, server_id, port_id):
        """Detach a port from a server.

        DELETE /v2.1/servers/{server_id}/os-interface/{port_id}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-interface/{port_id}"
        self._delete(url)

    # ── Attached Volumes ─────────────────────────────────────────

    def list_attached_volumes(self, server_id):
        """List volumes attached to a server.

        GET /v2.1/servers/{server_id}/os-volume_attachments
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-volume_attachments"
        resp = self._get(url)
        return resp.json()["volumeAttachments"]

    def get_attached_volume(self, server_id, volume_id):
        """Get details of an attached volume.

        GET /v2.1/servers/{server_id}/os-volume_attachments/{volume_id}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-volume_attachments/{volume_id}"
        resp = self._get(url)
        return resp.json()["volumeAttachment"]

    def attach_volume(self, server_id, volume_id):
        """Attach a volume to a server. Server must be stopped.

        POST /v2.1/servers/{server_id}/os-volume_attachments
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-volume_attachments"
        resp = self._post(
            url, json={"volumeAttachment": {"volumeId": volume_id}}
        )
        return resp.json()["volumeAttachment"]

    def detach_volume(self, server_id, volume_id):
        """Detach a volume from a server. Server must be stopped.

        DELETE /v2.1/servers/{server_id}/os-volume_attachments/{volume_id}
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/os-volume_attachments/{volume_id}"
        self._delete(url)

    # ── Monitoring Graphs ────────────────────────────────────────

    def get_cpu_graph(
        self, server_id, start_date_raw=None, end_date_raw=None, mode=None
    ):
        """Get CPU usage graph data.

        GET /v2.1/servers/{server_id}/rrd/cpu
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/rrd/cpu"
        params = {}
        if start_date_raw:
            params["start_date_raw"] = start_date_raw
        if end_date_raw:
            params["end_date_raw"] = end_date_raw
        if mode:
            params["mode"] = mode
        resp = self._get(url, params=params)
        return resp.json()["cpu"]

    def get_disk_io_graph(
        self,
        server_id,
        device=None,
        start_date_raw=None,
        end_date_raw=None,
        mode=None,
    ):
        """Get disk I/O graph data.

        GET /v2.1/servers/{server_id}/rrd/disk
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/rrd/disk"
        params = {}
        if device:
            params["device"] = device
        if start_date_raw:
            params["start_date_raw"] = start_date_raw
        if end_date_raw:
            params["end_date_raw"] = end_date_raw
        if mode:
            params["mode"] = mode
        resp = self._get(url, params=params)
        return resp.json()["disk"]

    def get_traffic_graph(
        self,
        server_id,
        port_id,
        start_date_raw=None,
        end_date_raw=None,
        mode=None,
    ):
        """Get network traffic graph data.

        GET /v2.1/servers/{server_id}/rrd/interface
        """
        url = f"{self._base_url}/v2.1/servers/{server_id}/rrd/interface"
        params = {"port_id": port_id}
        if start_date_raw:
            params["start_date_raw"] = start_date_raw
        if end_date_raw:
            params["end_date_raw"] = end_date_raw
        if mode:
            params["mode"] = mode
        resp = self._get(url, params=params)
        return resp.json()["interface"]
