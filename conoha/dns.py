"""ConoHa DNS API service."""

from .base import BaseService


class DNSService(BaseService):
    """DNS API: domain and record management.

    Base URL: https://dns-service.{region}.conoha.io
    """

    def __init__(self, client):
        super().__init__(client)
        self._base_url = client._get_endpoint("dns")

    # ── Domains ──────────────────────────────────────────────────

    def list_domains(self, limit=None, offset=None, sort_type=None,
                     sort_key=None):
        """List domains.

        GET /v1/domains
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort_type:
            params["sort_type"] = sort_type
        if sort_key:
            params["sort_key"] = sort_key
        url = f"{self._base_url}/v1/domains"
        resp = self._get(url, params=params)
        return resp.json()["domains"]

    def get_domain(self, domain_id):
        """Get domain details.

        GET /v1/domains/{domain_id}
        """
        url = f"{self._base_url}/v1/domains/{domain_id}"
        resp = self._get(url)
        return resp.json()

    def create_domain(self, name, ttl, email):
        """Register a domain.

        POST /v1/domains
        name: domain name (e.g. "example.com.")
        """
        body = {"name": name, "ttl": ttl, "email": email}
        url = f"{self._base_url}/v1/domains"
        resp = self._post(url, json=body)
        return resp.json()

    def update_domain(self, domain_id, ttl=None, email=None):
        """Update domain information.

        PUT /v1/domains/{domain_id}
        """
        body = {}
        if ttl is not None:
            body["ttl"] = ttl
        if email is not None:
            body["email"] = email
        url = f"{self._base_url}/v1/domains/{domain_id}"
        resp = self._put(url, json=body)
        return resp.json()

    def delete_domain(self, domain_id):
        """Delete a domain.

        DELETE /v1/domains/{domain_id}
        """
        url = f"{self._base_url}/v1/domains/{domain_id}"
        self._delete(url)

    # ── Records ──────────────────────────────────────────────────

    def list_records(self, domain_id):
        """List DNS records for a domain.

        GET /v1/domains/{domain_id}/records
        """
        url = f"{self._base_url}/v1/domains/{domain_id}/records"
        resp = self._get(url)
        return resp.json()["records"]

    def get_record(self, domain_id, record_id):
        """Get record details.

        GET /v1/domains/{domain_id}/records/{record_id}
        """
        url = f"{self._base_url}/v1/domains/{domain_id}/records/{record_id}"
        resp = self._get(url)
        return resp.json()

    def create_record(self, domain_id, name, record_type, data, ttl=None,
                      priority=None):
        """Create a DNS record.

        POST /v1/domains/{domain_id}/records
        record_type: A, AAAA, CNAME, MX, TXT, SRV, NS, etc.
        """
        body = {"name": name, "type": record_type, "data": data}
        if ttl is not None:
            body["ttl"] = ttl
        if priority is not None:
            body["priority"] = priority
        url = f"{self._base_url}/v1/domains/{domain_id}/records"
        resp = self._post(url, json=body)
        return resp.json()

    def update_record(self, domain_id, record_id, name=None, data=None,
                      ttl=None, priority=None):
        """Update a DNS record.

        PUT /v1/domains/{domain_id}/records/{record_id}
        """
        body = {}
        if name is not None:
            body["name"] = name
        if data is not None:
            body["data"] = data
        if ttl is not None:
            body["ttl"] = ttl
        if priority is not None:
            body["priority"] = priority
        url = f"{self._base_url}/v1/domains/{domain_id}/records/{record_id}"
        resp = self._put(url, json=body)
        return resp.json()

    def delete_record(self, domain_id, record_id):
        """Delete a DNS record.

        DELETE /v1/domains/{domain_id}/records/{record_id}
        """
        url = f"{self._base_url}/v1/domains/{domain_id}/records/{record_id}"
        self._delete(url)
