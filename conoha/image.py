"""ConoHa Image API service."""

from .base import BaseService


class ImageService(BaseService):
    """Image API: VM images, ISO images, image quota management.

    Base URL: https://image-service.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("image")

    # ── Images ───────────────────────────────────────────────────

    def list_images(self, limit=None, marker=None, visibility=None,
                    os_type=None, sort_key=None, sort_dir=None, name=None,
                    status=None):
        """List images.

        GET /v2/images
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        if visibility:
            params["visibility"] = visibility
        if os_type:
            params["os_type"] = os_type
        if sort_key:
            params["sort_key"] = sort_key
        if sort_dir:
            params["sort_dir"] = sort_dir
        if name:
            params["name"] = name
        if status:
            params["status"] = status
        url = f"{self._base_url}/v2/images"
        resp = self._get(url, params=params)
        return resp.json()["images"]

    def get_image(self, image_id):
        """Get image details.

        GET /v2/images/{image_id}
        """
        url = f"{self._base_url}/v2/images/{image_id}"
        resp = self._get(url)
        return resp.json()

    def delete_image(self, image_id):
        """Delete an image.

        DELETE /v2/images/{image_id}
        """
        url = f"{self._base_url}/v2/images/{image_id}"
        self._delete(url)

    # ── ISO Images ───────────────────────────────────────────────

    def create_iso_image(self, name):
        """Create an ISO image entry (metadata only, upload file separately).

        POST /v2/images
        """
        body = {
            "name": name,
            "disk_format": "iso",
            "hw_rescue_bus": "ide",
            "hw_rescue_device": "cdrom",
            "container_format": "bare",
        }
        url = f"{self._base_url}/v2/images"
        resp = self._post(url, json=body)
        return resp.json()

    def upload_iso_image(self, image_id, file_data):
        """Upload ISO image file data.

        PUT /v2/images/{image_id}/file
        """
        url = f"{self._base_url}/v2/images/{image_id}/file"
        self._put(
            url,
            data=file_data,
            extra_headers={"Content-Type": "application/octet-stream"},
        )

    # ── Image Quota & Usage ──────────────────────────────────────

    def get_image_usage(self):
        """Get total image storage usage in bytes.

        GET /v2/images/total
        """
        url = f"{self._base_url}/v2/images/total"
        resp = self._get(url)
        return resp.json()["images"]

    def get_image_quota(self):
        """Get image storage quota.

        GET /v2/quota
        """
        url = f"{self._base_url}/v2/quota"
        resp = self._get(url)
        return resp.json()["quota"]

    def update_image_quota(self, image_size_gb):
        """Update image storage quota.

        PUT /v2/quota
        Sizes: 50GB (default), 550GB, 1050GB, etc. (500GB increments)
        """
        url = f"{self._base_url}/v2/quota"
        body = {"quota": {"image_size": f"{image_size_gb}GB"}}
        resp = self._put(url, json=body)
        return resp.json()["quota"]
