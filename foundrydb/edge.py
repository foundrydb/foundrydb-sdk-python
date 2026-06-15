"""
FoundryDB SDK - Edge Gateway API (sync and async).

The edge gateway sits in front of app services and provides custom domains
with automated TLS, path-based caching, token-bucket rate limiting, and a
web application firewall (WAF). Every app service has an edge status
resource; domains and settings are managed per app service.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .client import AsyncHTTPClient, HTTPClient
from .types import EdgeCacheRule, EdgeDomain, EdgeRateLimit, EdgeSettings, EdgeStatus


class EdgeAPI:
    """Manages the edge gateway surface for app services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list_domains(self, app_service_id: str) -> List[EdgeDomain]:
        """List all custom domains attached to an app service."""
        data = self._http.get(f"/app-services/{app_service_id}/domains")
        return [EdgeDomain.from_dict(d) for d in data.get("domains", [])]

    def create_domain(self, app_service_id: str, domain: str) -> EdgeDomain:
        """Add a custom domain to an app service.

        The domain is created in ``pending_verification`` status. The platform
        verifies CNAME ownership in the background and, once verified,
        provisions a TLS certificate. Call :meth:`verify_domain` to trigger an
        immediate verification pass instead of waiting for the background
        worker.
        """
        data = self._http.post(
            f"/app-services/{app_service_id}/domains",
            {"domain": domain},
        )
        return EdgeDomain.from_dict(data)

    def verify_domain(self, app_service_id: str, domain_id: str) -> EdgeDomain:
        """Requeue a pending or failed domain for an immediate verification pass.

        Returns the updated domain after the verification pass is enqueued.
        """
        data = self._http.post(
            f"/app-services/{app_service_id}/domains/{domain_id}/verify",
        )
        return EdgeDomain.from_dict(data)

    def delete_domain(self, app_service_id: str, domain_id: str) -> None:
        """Remove a custom domain from an app service.

        The TLS certificate is revoked and DNS records are removed. A 404
        response is treated as success (idempotent).
        """
        try:
            self._http.delete(f"/app-services/{app_service_id}/domains/{domain_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return
            raise

    def get_status(self, app_service_id: str) -> EdgeStatus:
        """Return the edge overview for an app service.

        Includes whether the edge tier is enabled, the home PoP, the CNAME
        target that custom domains point at, the desired-state config version,
        and the per-PoP convergence status.
        """
        data = self._http.get(f"/app-services/{app_service_id}/edge")
        return EdgeStatus.from_dict(data)

    def update_settings(
        self,
        app_service_id: str,
        *,
        cache_rules: Optional[List[EdgeCacheRule]] = None,
        rate_limit: Optional[EdgeRateLimit] = None,
        waf_mode: Optional[str] = None,
    ) -> EdgeSettings:
        """Replace the customer-tunable edge settings for an app service.

        Domains and origin are platform-derived and cannot be set here.
        Returns the updated settings and the config version the fleet will
        converge on.

        Args:
            app_service_id: App service ID.
            cache_rules: Path-prefix cache rules. Pass an empty list to clear.
            rate_limit: Token-bucket rate limit.
            waf_mode: ``"off"`` or ``"detect"``.
        """
        body: Dict[str, object] = {}
        if cache_rules is not None:
            body["cache_rules"] = [r.to_dict() for r in cache_rules]
        if rate_limit is not None:
            body["rate_limit"] = rate_limit.to_dict()
        if waf_mode is not None:
            body["waf_mode"] = waf_mode
        data = self._http.put(f"/app-services/{app_service_id}/edge/settings", body)
        return EdgeSettings.from_dict(data)


class AsyncEdgeAPI:
    """Manages the edge gateway surface for app services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list_domains(self, app_service_id: str) -> List[EdgeDomain]:
        """List all custom domains attached to an app service."""
        data = await self._http.get(f"/app-services/{app_service_id}/domains")
        return [EdgeDomain.from_dict(d) for d in data.get("domains", [])]

    async def create_domain(self, app_service_id: str, domain: str) -> EdgeDomain:
        """Add a custom domain to an app service."""
        data = await self._http.post(
            f"/app-services/{app_service_id}/domains",
            {"domain": domain},
        )
        return EdgeDomain.from_dict(data)

    async def verify_domain(self, app_service_id: str, domain_id: str) -> EdgeDomain:
        """Requeue a pending or failed domain for an immediate verification pass."""
        data = await self._http.post(
            f"/app-services/{app_service_id}/domains/{domain_id}/verify",
        )
        return EdgeDomain.from_dict(data)

    async def delete_domain(self, app_service_id: str, domain_id: str) -> None:
        """Remove a custom domain from an app service (idempotent)."""
        try:
            await self._http.delete(f"/app-services/{app_service_id}/domains/{domain_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return
            raise

    async def get_status(self, app_service_id: str) -> EdgeStatus:
        """Return the edge overview for an app service."""
        data = await self._http.get(f"/app-services/{app_service_id}/edge")
        return EdgeStatus.from_dict(data)

    async def update_settings(
        self,
        app_service_id: str,
        *,
        cache_rules: Optional[List[EdgeCacheRule]] = None,
        rate_limit: Optional[EdgeRateLimit] = None,
        waf_mode: Optional[str] = None,
    ) -> EdgeSettings:
        """Replace the customer-tunable edge settings for an app service."""
        body: Dict[str, object] = {}
        if cache_rules is not None:
            body["cache_rules"] = [r.to_dict() for r in cache_rules]
        if rate_limit is not None:
            body["rate_limit"] = rate_limit.to_dict()
        if waf_mode is not None:
            body["waf_mode"] = waf_mode
        data = await self._http.put(f"/app-services/{app_service_id}/edge/settings", body)
        return EdgeSettings.from_dict(data)
