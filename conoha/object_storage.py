"""ConoHa Object Storage API service."""

import hashlib
import hmac
import json
import time

from .base import BaseService


class ObjectStorageService(BaseService):
    """Object Storage API: containers and objects management.

    Base URL: https://object-storage.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("object_storage")

    def _account_url(self, path=""):
        return f"{self._base_url}/v1/AUTH_{self._tenant_id}{path}"

    # ── Account ──────────────────────────────────────────────────

    def get_account_info(self):
        """Get account metadata (container count, bytes used, etc.).

        HEAD /v1/AUTH_{tenant_id}
        """
        url = self._account_url()
        resp = self._head(url)
        return {
            "container_count": resp.headers.get("x-account-container-count"),
            "object_count": resp.headers.get("x-account-object-count"),
            "bytes_used": resp.headers.get("x-account-bytes-used"),
        }

    def set_account_quota(self, size_gb):
        """Set account storage quota.

        POST /v1/AUTH_{tenant_id}
        size_gb: capacity in GB (minimum 100, in 100GB increments)
        """
        url = self._account_url()
        self._post(
            url,
            extra_headers={
                "X-Account-Meta-Quota-Giga-Bytes": str(size_gb)
            },
        )

    # ── Containers ───────────────────────────────────────────────

    def list_containers(self, limit=None, marker=None, end_marker=None,
                        prefix=None, delimiter=None, reverse=None):
        """List containers.

        GET /v1/AUTH_{tenant_id}
        """
        params = {"format": "json"}
        if limit is not None:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        if end_marker:
            params["end_marker"] = end_marker
        if prefix:
            params["prefix"] = prefix
        if delimiter:
            params["delimiter"] = delimiter
        if reverse is not None:
            params["reverse"] = reverse
        url = self._account_url()
        resp = self._get(url, params=params)
        return resp.json()

    def get_container_metadata(self, container):
        """Get container metadata via HEAD request.

        HEAD /v1/AUTH_{tenant_id}/{container}
        """
        url = self._account_url(f"/{container}")
        resp = self._head(url)
        return {
            "object_count": resp.headers.get("x-container-object-count"),
            "bytes_used": resp.headers.get("x-container-bytes-used"),
            "bytes_used_actual": resp.headers.get(
                "x-container-bytes-used-actual"
            ),
        }

    def create_container(self, container):
        """Create a container.

        PUT /v1/AUTH_{tenant_id}/{container}
        """
        url = self._account_url(f"/{container}")
        self._put(url)

    def delete_container(self, container):
        """Delete a container. Must be empty.

        DELETE /v1/AUTH_{tenant_id}/{container}
        """
        url = self._account_url(f"/{container}")
        self._delete(url)

    # ── Objects ──────────────────────────────────────────────────

    def list_objects(self, container, limit=None, marker=None,
                     end_marker=None, prefix=None, delimiter=None,
                     reverse=None):
        """List objects in a container.

        GET /v1/AUTH_{tenant_id}/{container}
        """
        params = {"format": "json"}
        if limit is not None:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        if end_marker:
            params["end_marker"] = end_marker
        if prefix:
            params["prefix"] = prefix
        if delimiter:
            params["delimiter"] = delimiter
        if reverse is not None:
            params["reverse"] = reverse
        url = self._account_url(f"/{container}")
        resp = self._get(url, params=params)
        return resp.json()

    def upload_object(self, container, object_name, data, content_type=None):
        """Upload an object (max 5GB).

        PUT /v1/AUTH_{tenant_id}/{container}/{object_name}
        """
        url = self._account_url(f"/{container}/{object_name}")
        extra_headers = {}
        if content_type:
            extra_headers["Content-Type"] = content_type
        self._put(url, data=data, extra_headers=extra_headers or None)

    def download_object(self, container, object_name):
        """Download an object.

        GET /v1/AUTH_{tenant_id}/{container}/{object_name}
        Returns response object (use .content for binary data).
        """
        url = self._account_url(f"/{container}/{object_name}")
        return self._get(url)

    def delete_object(self, container, object_name):
        """Delete an object.

        DELETE /v1/AUTH_{tenant_id}/{container}/{object_name}
        """
        url = self._account_url(f"/{container}/{object_name}")
        self._delete(url)

    def copy_object(self, src_container, src_object, dst_container, dst_object):
        """Copy an object to a new location.

        COPY /v1/AUTH_{tenant_id}/{src_container}/{src_object}
        Uses the X-Copy-To header to specify the destination.
        """
        url = self._account_url(f"/{src_container}/{src_object}")
        self._request(
            "COPY", url,
            extra_headers={
                "Destination": f"{dst_container}/{dst_object}",
            },
        )

    def schedule_object_deletion(self, container, object_name, seconds):
        """Schedule an object for automatic deletion after N seconds.

        POST /v1/AUTH_{tenant_id}/{container}/{object_name}
        """
        url = self._account_url(f"/{container}/{object_name}")
        self._post(
            url,
            extra_headers={"X-Delete-After": str(seconds)},
        )

    def get_object_metadata(self, container, object_name):
        """Get object metadata via HEAD request.

        HEAD /v1/AUTH_{tenant_id}/{container}/{object_name}
        """
        url = self._account_url(f"/{container}/{object_name}")
        resp = self._head(url)
        return dict(resp.headers)

    # ── Web Publishing ────────────────────────────────────────

    def enable_web_publishing(self, container):
        """Enable public web publishing for a container.

        POST /v1/AUTH_{tenant_id}/{container}
        Sets X-Container-Read to .r:* for anonymous read access.
        """
        url = self._account_url(f"/{container}")
        self._post(url, extra_headers={"X-Container-Read": ".r:*"})

    def disable_web_publishing(self, container):
        """Disable public web publishing for a container.

        POST /v1/AUTH_{tenant_id}/{container}
        """
        url = self._account_url(f"/{container}")
        self._post(url, extra_headers={"X-Container-Read": ""})

    # ── Versioning ────────────────────────────────────────────

    def enable_versioning(self, container, versions_container):
        """Enable object versioning on a container.

        POST /v1/AUTH_{tenant_id}/{container}
        Old versions are stored in versions_container.
        """
        url = self._account_url(f"/{container}")
        self._post(
            url,
            extra_headers={"X-Versions-Location": versions_container},
        )

    def disable_versioning(self, container):
        """Disable object versioning on a container.

        POST /v1/AUTH_{tenant_id}/{container}
        Uses X-Remove-Versions-Location to remove the versioning setting.
        """
        url = self._account_url(f"/{container}")
        self._post(url, extra_headers={"X-Remove-Versions-Location": "x"})

    # ── Dynamic Large Object (DLO) ───────────────────────────

    def create_dlo_manifest(self, container, manifest_name, object_prefix,
                            content_type=None):
        """Create a Dynamic Large Object manifest.

        PUT /v1/AUTH_{tenant_id}/{container}/{manifest_name}
        Segments are found by prefix in the same container.
        """
        url = self._account_url(f"/{container}/{manifest_name}")
        headers = {"X-Object-Manifest": f"{container}/{object_prefix}"}
        if content_type:
            headers["Content-Type"] = content_type
        self._put(url, data=b"", extra_headers=headers)

    # ── Static Large Object (SLO) ────────────────────────────

    def create_slo_manifest(self, container, manifest_name, segments,
                            content_type=None):
        """Create a Static Large Object manifest.

        PUT /v1/AUTH_{tenant_id}/{container}/{manifest_name}?multipart-manifest=put
        segments: list of dicts with keys 'path', 'etag', 'size_bytes'.
        """
        url = self._account_url(f"/{container}/{manifest_name}")
        params = {"multipart-manifest": "put"}
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        self._put(
            url,
            params=params,
            data=json.dumps(segments).encode("utf-8"),
            extra_headers=headers or None,
        )

    # ── Temporary URL ─────────────────────────────────────────

    def set_temp_url_key(self, key, key_index=1):
        """Set the temporary URL key for the account.

        POST /v1/AUTH_{tenant_id}
        key_index: 1 or 2 (supports two keys for rotation).
        """
        url = self._account_url()
        header_name = "X-Account-Meta-Temp-URL-Key"
        if key_index == 2:
            header_name = "X-Account-Meta-Temp-URL-Key-2"
        self._post(url, extra_headers={header_name: key})

    def generate_temp_url(self, container, object_name, seconds,
                          method="GET", key=None):
        """Generate a temporary URL for an object.

        Client-side HMAC computation; requires temp_url_key set on account.
        """
        if key is None:
            raise ValueError("key is required to generate a temporary URL")

        expires = int(time.time()) + seconds
        path = f"/v1/AUTH_{self._tenant_id}/{container}/{object_name}"
        sig_body = f"{method}\n{expires}\n{path}"
        sig = hmac.new(
            key.encode("utf-8"),
            sig_body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        base = self._account_url(f"/{container}/{object_name}")
        return f"{base}?temp_url_sig={sig}&temp_url_expires={expires}"
