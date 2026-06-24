"""
FoundryDB SDK - Edge Gateway API (sync and async).

The edge gateway sits in front of app services and provides custom domains
with automated TLS, path-based caching (with stale-while-revalidate,
stale-if-error, custom cache keys and request collapsing), token-bucket rate
limiting, a web application firewall (WAF) with paranoia levels and rule
exclusions, access controls (JWT, signed URLs, API keys), and security
hardening (DDoS, bot management, account-takeover protection). It also exposes
cache purge, analytics, an append-only config version history with rollback,
staged config rollouts, and access-log drains. Every app service has an edge
status resource; domains and settings are managed per app service.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import AsyncHTTPClient, HTTPClient
from .types import (
    EdgeAnalytics,
    EdgeAPIKeyAuthRequest,
    EdgeATOProtection,
    EdgeBotManagement,
    EdgeCachePurgeResult,
    EdgeCacheRule,
    EdgeConfigVersions,
    EdgeDDoSProfile,
    EdgeDomain,
    EdgeJWTAuth,
    EdgeLogDrain,
    EdgeLogDrainTestResult,
    EdgeRateLimit,
    EdgeRedactionPolicy,
    EdgeRollbackResult,
    EdgeRolloutStatus,
    EdgeSettings,
    EdgeSignedURLs,
    EdgeStatus,
    EdgeWAFExclusion,
)


def _build_settings_body(
    *,
    cache_rules: Optional[List[EdgeCacheRule]],
    rate_limit: Optional[EdgeRateLimit],
    waf_mode: Optional[str],
    jwt_auth: Optional[EdgeJWTAuth],
    signed_urls: Optional[EdgeSignedURLs],
    api_key_auth: Optional[EdgeAPIKeyAuthRequest],
    waf_paranoia_level: Optional[int],
    waf_rule_exclusions: Optional[List[EdgeWAFExclusion]],
    ddos_profile: Optional[EdgeDDoSProfile],
    bot_management: Optional[EdgeBotManagement],
    ato_protection: Optional[EdgeATOProtection],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if cache_rules is not None:
        body["cache_rules"] = [r.to_dict() for r in cache_rules]
    if rate_limit is not None:
        body["rate_limit"] = rate_limit.to_dict()
    if waf_mode is not None:
        body["waf_mode"] = waf_mode
    if jwt_auth is not None:
        body["jwt_auth"] = jwt_auth.to_dict()
    if signed_urls is not None:
        body["signed_urls"] = signed_urls.to_dict()
    if api_key_auth is not None:
        body["api_key_auth"] = api_key_auth.to_dict()
    if waf_paranoia_level is not None:
        body["waf_paranoia_level"] = waf_paranoia_level
    if waf_rule_exclusions is not None:
        body["waf_rule_exclusions"] = [e.to_dict() for e in waf_rule_exclusions]
    if ddos_profile is not None:
        body["ddos_profile"] = ddos_profile.to_dict()
    if bot_management is not None:
        body["bot_management"] = bot_management.to_dict()
    if ato_protection is not None:
        body["ato_protection"] = ato_protection.to_dict()
    return body


def _log_drain_create_body(
    name: str,
    destination_type: str,
    configuration: Dict[str, Any],
    description: Optional[str],
    redaction_policy: Optional[EdgeRedactionPolicy],
    is_enabled: Optional[bool],
    export_interval_seconds: Optional[int],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "name": name,
        "destination_type": destination_type,
        "configuration": configuration,
    }
    if description is not None:
        body["description"] = description
    if redaction_policy is not None:
        body["redaction_policy"] = redaction_policy.to_dict()
    if is_enabled is not None:
        body["is_enabled"] = is_enabled
    if export_interval_seconds is not None:
        body["export_interval_seconds"] = export_interval_seconds
    return body


def _log_drain_update_body(
    name: Optional[str],
    description: Optional[str],
    destination_type: Optional[str],
    configuration: Optional[Dict[str, Any]],
    redaction_policy: Optional[EdgeRedactionPolicy],
    is_enabled: Optional[bool],
    export_interval_seconds: Optional[int],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if destination_type is not None:
        body["destination_type"] = destination_type
    if configuration is not None:
        body["configuration"] = configuration
    if redaction_policy is not None:
        body["redaction_policy"] = redaction_policy.to_dict()
    if is_enabled is not None:
        body["is_enabled"] = is_enabled
    if export_interval_seconds is not None:
        body["export_interval_seconds"] = export_interval_seconds
    return body


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

    def get_settings(self, app_service_id: str) -> EdgeSettings:
        """Return the customer-tunable edge settings currently stored for an
        app service, plus the desired-state config version the fleet converges
        on. Secret material (Basic Auth hashes, API key hashes) is never
        returned."""
        data = self._http.get(f"/app-services/{app_service_id}/edge/settings")
        return EdgeSettings.from_dict(data)

    def update_settings(
        self,
        app_service_id: str,
        *,
        cache_rules: Optional[List[EdgeCacheRule]] = None,
        rate_limit: Optional[EdgeRateLimit] = None,
        waf_mode: Optional[str] = None,
        jwt_auth: Optional[EdgeJWTAuth] = None,
        signed_urls: Optional[EdgeSignedURLs] = None,
        api_key_auth: Optional[EdgeAPIKeyAuthRequest] = None,
        waf_paranoia_level: Optional[int] = None,
        waf_rule_exclusions: Optional[List[EdgeWAFExclusion]] = None,
        ddos_profile: Optional[EdgeDDoSProfile] = None,
        bot_management: Optional[EdgeBotManagement] = None,
        ato_protection: Optional[EdgeATOProtection] = None,
    ) -> EdgeSettings:
        """Replace the customer-tunable edge settings for an app service.

        Domains and origin are platform-derived and cannot be set here. Each
        list/object field replaces the stored value wholesale; an omitted field
        leaves the corresponding setting unchanged. Returns the updated settings
        and the config version the fleet will converge on.

        Args:
            app_service_id: App service ID.
            cache_rules: Path-prefix cache rules (with optional cache-depth
                fields). Pass an empty list to clear.
            rate_limit: Token-bucket rate limit.
            waf_mode: ``"off"``, ``"detect"`` or ``"block"``.
            jwt_auth: Edge JWT validation policy.
            signed_urls: Signed-URL access policy (secret referenced by name).
            api_key_auth: Inbound API-key authentication (plaintext keys are
                write-only and hashed server-side).
            waf_paranoia_level: Managed WAF paranoia level (1..4; 0 = default).
            waf_rule_exclusions: Managed WAF rule/target exclusions.
            ddos_profile: Per-IP volumetric protection.
            bot_management: Bot detection policy.
            ato_protection: Account-takeover protection policy.
        """
        body = _build_settings_body(
            cache_rules=cache_rules,
            rate_limit=rate_limit,
            waf_mode=waf_mode,
            jwt_auth=jwt_auth,
            signed_urls=signed_urls,
            api_key_auth=api_key_auth,
            waf_paranoia_level=waf_paranoia_level,
            waf_rule_exclusions=waf_rule_exclusions,
            ddos_profile=ddos_profile,
            bot_management=bot_management,
            ato_protection=ato_protection,
        )
        data = self._http.put(f"/app-services/{app_service_id}/edge/settings", body)
        return EdgeSettings.from_dict(data)

    # ---- Cache purge ----

    def purge_cache(
        self,
        app_service_id: str,
        *,
        all: bool = False,
        paths: Optional[List[str]] = None,
    ) -> EdgeCachePurgeResult:
        """Flush the app's edge cache across its serving PoP nodes, either
        entirely (``all=True``) or for the listed absolute ``paths``; set exactly
        one. The purge rolls across nodes one at a time in the background, so the
        result reports the plan (planned node count and ids)."""
        body: Dict[str, Any] = {}
        if all:
            body["all"] = True
        if paths:
            body["paths"] = list(paths)
        data = self._http.post(f"/app-services/{app_service_id}/edge/cache/purge", body)
        return EdgeCachePurgeResult.from_dict(data)

    # ---- Analytics ----

    def get_analytics(
        self, app_service_id: str, *, window_minutes: int = 0
    ) -> EdgeAnalytics:
        """Return the account-scoped edge analytics summary for an app over
        ``window_minutes`` (0 uses the server default of 60 minutes), folded
        across the app's PoPs with a per-PoP breakdown."""
        path = f"/app-services/{app_service_id}/edge/analytics"
        if window_minutes > 0:
            path += f"?window_minutes={window_minutes}"
        data = self._http.get(path)
        return EdgeAnalytics.from_dict(data)

    # ---- Config version history / rollback ----

    def list_config_versions(self, app_service_id: str) -> EdgeConfigVersions:
        """Return the append-only version history of an app service's edge
        configuration, newest first, plus the live active version."""
        data = self._http.get(f"/app-services/{app_service_id}/edge/versions")
        return EdgeConfigVersions.from_dict(data)

    def rollback_config(
        self,
        app_service_id: str,
        *,
        to_version: Optional[int] = None,
        to: Optional[str] = None,
    ) -> EdgeRollbackResult:
        """Roll an app service's edge configuration back to a prior version.
        Supply exactly one of ``to_version`` (an explicit positive version) or
        ``to="previous"``. The rollback restores the target version's
        customer-settable subset as a NEW forward version; it never mutates the
        history. The fleet converges asynchronously."""
        body: Dict[str, Any] = {}
        if to_version is not None:
            body["to_version"] = to_version
        if to is not None:
            body["to"] = to
        data = self._http.post(f"/app-services/{app_service_id}/edge/rollback", body)
        return EdgeRollbackResult.from_dict(data)

    # ---- Staged config rollouts ----

    def get_rollout(self, app_service_id: str) -> EdgeRolloutStatus:
        """Return the app service's current staged config rollout (the active
        one, or the most recent terminal one), or ``active=False`` with no
        rollout when the app has never had one."""
        data = self._http.get(f"/app-services/{app_service_id}/edge/rollout")
        return EdgeRolloutStatus.from_dict(data)

    def promote_rollout(self, app_service_id: str) -> None:
        """Promote a holding canary rollout so the platform fans the canary
        version out to the rest of the fleet. Only an active rollout in the
        canary phase can be promoted."""
        self._http.post(f"/app-services/{app_service_id}/edge/rollout/promote")

    def abort_rollout(self, app_service_id: str, *, reason: str = "") -> None:
        """Abort an active rollout. The rest of the fleet keeps serving the
        prior version; the canary subset can be recovered with
        :meth:`rollback_config`. ``reason`` is an optional operator note."""
        body: Dict[str, Any] = {}
        if reason:
            body["reason"] = reason
        self._http.post(f"/app-services/{app_service_id}/edge/rollout/abort", body)

    # ---- Access-log drains ----

    def list_log_drains(self, app_service_id: str) -> List[EdgeLogDrain]:
        """List the app's edge access-log drains."""
        data = self._http.get(f"/app-services/{app_service_id}/edge/log-drains")
        return [EdgeLogDrain.from_dict(d) for d in data.get("drains", [])]

    def create_log_drain(
        self,
        app_service_id: str,
        *,
        name: str,
        destination_type: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        redaction_policy: Optional[EdgeRedactionPolicy] = None,
        is_enabled: Optional[bool] = None,
        export_interval_seconds: Optional[int] = None,
    ) -> EdgeLogDrain:
        """Create an edge access-log drain. Configuration is destination-specific
        (s3: endpoint/region/bucket/prefix/access_key_id/secret_access_key;
        webhook: url/auth_header_name/auth_header_value)."""
        body = _log_drain_create_body(
            name, destination_type, configuration, description,
            redaction_policy, is_enabled, export_interval_seconds,
        )
        data = self._http.post(f"/app-services/{app_service_id}/edge/log-drains", body)
        return EdgeLogDrain.from_dict(data)

    def get_log_drain(self, app_service_id: str, drain_id: str) -> EdgeLogDrain:
        """Return one edge access-log drain."""
        data = self._http.get(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}"
        )
        return EdgeLogDrain.from_dict(data)

    def update_log_drain(
        self,
        app_service_id: str,
        drain_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        destination_type: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        redaction_policy: Optional[EdgeRedactionPolicy] = None,
        is_enabled: Optional[bool] = None,
        export_interval_seconds: Optional[int] = None,
    ) -> EdgeLogDrain:
        """Partially update an edge access-log drain; omitted fields keep their
        value."""
        body = _log_drain_update_body(
            name, description, destination_type, configuration,
            redaction_policy, is_enabled, export_interval_seconds,
        )
        data = self._http.put(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}", body
        )
        return EdgeLogDrain.from_dict(data)

    def delete_log_drain(self, app_service_id: str, drain_id: str) -> None:
        """Delete an edge access-log drain, stopping all future exports."""
        self._http.delete(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}"
        )

    def test_log_drain(
        self, app_service_id: str, drain_id: str
    ) -> EdgeLogDrainTestResult:
        """Verify connectivity to the drain's destination without sending real
        log data."""
        data = self._http.post(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}/test"
        )
        return EdgeLogDrainTestResult.from_dict(data)


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

    async def get_settings(self, app_service_id: str) -> EdgeSettings:
        """Return the customer-tunable edge settings currently stored for an
        app service. Secret material is never returned."""
        data = await self._http.get(f"/app-services/{app_service_id}/edge/settings")
        return EdgeSettings.from_dict(data)

    async def update_settings(
        self,
        app_service_id: str,
        *,
        cache_rules: Optional[List[EdgeCacheRule]] = None,
        rate_limit: Optional[EdgeRateLimit] = None,
        waf_mode: Optional[str] = None,
        jwt_auth: Optional[EdgeJWTAuth] = None,
        signed_urls: Optional[EdgeSignedURLs] = None,
        api_key_auth: Optional[EdgeAPIKeyAuthRequest] = None,
        waf_paranoia_level: Optional[int] = None,
        waf_rule_exclusions: Optional[List[EdgeWAFExclusion]] = None,
        ddos_profile: Optional[EdgeDDoSProfile] = None,
        bot_management: Optional[EdgeBotManagement] = None,
        ato_protection: Optional[EdgeATOProtection] = None,
    ) -> EdgeSettings:
        """Replace the customer-tunable edge settings for an app service."""
        body = _build_settings_body(
            cache_rules=cache_rules,
            rate_limit=rate_limit,
            waf_mode=waf_mode,
            jwt_auth=jwt_auth,
            signed_urls=signed_urls,
            api_key_auth=api_key_auth,
            waf_paranoia_level=waf_paranoia_level,
            waf_rule_exclusions=waf_rule_exclusions,
            ddos_profile=ddos_profile,
            bot_management=bot_management,
            ato_protection=ato_protection,
        )
        data = await self._http.put(f"/app-services/{app_service_id}/edge/settings", body)
        return EdgeSettings.from_dict(data)

    # ---- Cache purge ----

    async def purge_cache(
        self,
        app_service_id: str,
        *,
        all: bool = False,
        paths: Optional[List[str]] = None,
    ) -> EdgeCachePurgeResult:
        """Flush the app's edge cache across its serving PoP nodes."""
        body: Dict[str, Any] = {}
        if all:
            body["all"] = True
        if paths:
            body["paths"] = list(paths)
        data = await self._http.post(
            f"/app-services/{app_service_id}/edge/cache/purge", body
        )
        return EdgeCachePurgeResult.from_dict(data)

    # ---- Analytics ----

    async def get_analytics(
        self, app_service_id: str, *, window_minutes: int = 0
    ) -> EdgeAnalytics:
        """Return the account-scoped edge analytics summary for an app."""
        path = f"/app-services/{app_service_id}/edge/analytics"
        if window_minutes > 0:
            path += f"?window_minutes={window_minutes}"
        data = await self._http.get(path)
        return EdgeAnalytics.from_dict(data)

    # ---- Config version history / rollback ----

    async def list_config_versions(self, app_service_id: str) -> EdgeConfigVersions:
        """Return the append-only edge config version history."""
        data = await self._http.get(f"/app-services/{app_service_id}/edge/versions")
        return EdgeConfigVersions.from_dict(data)

    async def rollback_config(
        self,
        app_service_id: str,
        *,
        to_version: Optional[int] = None,
        to: Optional[str] = None,
    ) -> EdgeRollbackResult:
        """Roll an app service's edge configuration back to a prior version."""
        body: Dict[str, Any] = {}
        if to_version is not None:
            body["to_version"] = to_version
        if to is not None:
            body["to"] = to
        data = await self._http.post(
            f"/app-services/{app_service_id}/edge/rollback", body
        )
        return EdgeRollbackResult.from_dict(data)

    # ---- Staged config rollouts ----

    async def get_rollout(self, app_service_id: str) -> EdgeRolloutStatus:
        """Return the app service's current staged config rollout."""
        data = await self._http.get(f"/app-services/{app_service_id}/edge/rollout")
        return EdgeRolloutStatus.from_dict(data)

    async def promote_rollout(self, app_service_id: str) -> None:
        """Promote a holding canary rollout to the rest of the fleet."""
        await self._http.post(f"/app-services/{app_service_id}/edge/rollout/promote")

    async def abort_rollout(self, app_service_id: str, *, reason: str = "") -> None:
        """Abort an active rollout. ``reason`` is an optional operator note."""
        body: Dict[str, Any] = {}
        if reason:
            body["reason"] = reason
        await self._http.post(
            f"/app-services/{app_service_id}/edge/rollout/abort", body
        )

    # ---- Access-log drains ----

    async def list_log_drains(self, app_service_id: str) -> List[EdgeLogDrain]:
        """List the app's edge access-log drains."""
        data = await self._http.get(f"/app-services/{app_service_id}/edge/log-drains")
        return [EdgeLogDrain.from_dict(d) for d in data.get("drains", [])]

    async def create_log_drain(
        self,
        app_service_id: str,
        *,
        name: str,
        destination_type: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        redaction_policy: Optional[EdgeRedactionPolicy] = None,
        is_enabled: Optional[bool] = None,
        export_interval_seconds: Optional[int] = None,
    ) -> EdgeLogDrain:
        """Create an edge access-log drain."""
        body = _log_drain_create_body(
            name, destination_type, configuration, description,
            redaction_policy, is_enabled, export_interval_seconds,
        )
        data = await self._http.post(
            f"/app-services/{app_service_id}/edge/log-drains", body
        )
        return EdgeLogDrain.from_dict(data)

    async def get_log_drain(self, app_service_id: str, drain_id: str) -> EdgeLogDrain:
        """Return one edge access-log drain."""
        data = await self._http.get(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}"
        )
        return EdgeLogDrain.from_dict(data)

    async def update_log_drain(
        self,
        app_service_id: str,
        drain_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        destination_type: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        redaction_policy: Optional[EdgeRedactionPolicy] = None,
        is_enabled: Optional[bool] = None,
        export_interval_seconds: Optional[int] = None,
    ) -> EdgeLogDrain:
        """Partially update an edge access-log drain."""
        body = _log_drain_update_body(
            name, description, destination_type, configuration,
            redaction_policy, is_enabled, export_interval_seconds,
        )
        data = await self._http.put(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}", body
        )
        return EdgeLogDrain.from_dict(data)

    async def delete_log_drain(self, app_service_id: str, drain_id: str) -> None:
        """Delete an edge access-log drain."""
        await self._http.delete(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}"
        )

    async def test_log_drain(
        self, app_service_id: str, drain_id: str
    ) -> EdgeLogDrainTestResult:
        """Verify connectivity to the drain's destination."""
        data = await self._http.post(
            f"/app-services/{app_service_id}/edge/log-drains/{drain_id}/test"
        )
        return EdgeLogDrainTestResult.from_dict(data)
