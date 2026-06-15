"""
Tests for foundrydb.edge - EdgeAPI (sync) and AsyncEdgeAPI (async).
"""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from foundrydb.edge import AsyncEdgeAPI, EdgeAPI
from foundrydb.client import AsyncHTTPClient, HTTPClient
from foundrydb.types import (
    EdgeAppApplication,
    EdgeCacheRule,
    EdgeDomain,
    EdgeRateLimit,
    EdgeSettings,
    EdgeStatus,
    FoundryDBError,
)

BASE = "https://api.foundrydb.test"
APP = "app-001"
DOMAIN_ID = "dom-001"

DOMAIN_PAYLOAD = {
    "id": DOMAIN_ID,
    "service_id": APP,
    "user_id": "user-001",
    "domain": "shop.acme.com",
    "status": "pending_verification",
    "cname_target": "edge.foundrydb.com",
    "certificate_id": None,
    "verification_checked_at": None,
    "error_message": None,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

ACTIVE_DOMAIN_PAYLOAD = dict(
    DOMAIN_PAYLOAD,
    status="active",
    certificate_id="cert-001",
    verification_checked_at="2026-01-01T01:00:00Z",
)

EDGE_STATUS_PAYLOAD = {
    "edge_enabled": True,
    "home_pop": "se-sto1",
    "cname_target": "edge.foundrydb.com",
    "config_version": 3,
    "applications": [
        {
            "zone": "se-sto1",
            "applied_version": 3,
            "status": "converged",
            "error_message": "",
        },
        {
            "zone": "fi-hel1",
            "applied_version": 2,
            "status": "converging",
            "error_message": "",
        },
    ],
}

EDGE_SETTINGS_PAYLOAD = {
    "cache_rules": [
        {"path_prefix": "/static/", "ttl_seconds": 86400},
    ],
    "rate_limit": {
        "requests_per_second": 100,
        "burst": 200,
        "key": "ip",
    },
    "waf_mode": "detect",
    "config_version": 4,
}


def make_sync_api() -> EdgeAPI:
    return EdgeAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncEdgeAPI:
    return AsyncEdgeAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestEdgeDomain:
    def test_from_dict_pending(self):
        d = EdgeDomain.from_dict(DOMAIN_PAYLOAD)
        assert d.id == DOMAIN_ID
        assert d.service_id == APP
        assert d.user_id == "user-001"
        assert d.domain == "shop.acme.com"
        assert d.status == "pending_verification"
        assert d.cname_target == "edge.foundrydb.com"
        assert d.certificate_id is None
        assert d.verification_checked_at is None
        assert d.error_message is None
        assert d.created_at == "2026-01-01T00:00:00Z"
        assert d.raw == DOMAIN_PAYLOAD

    def test_from_dict_active(self):
        d = EdgeDomain.from_dict(ACTIVE_DOMAIN_PAYLOAD)
        assert d.status == "active"
        assert d.certificate_id == "cert-001"
        assert d.verification_checked_at == "2026-01-01T01:00:00Z"


class TestEdgeCacheRule:
    def test_to_dict(self):
        rule = EdgeCacheRule(path_prefix="/static/", ttl_seconds=86400)
        assert rule.to_dict() == {"path_prefix": "/static/", "ttl_seconds": 86400}

    def test_from_dict(self):
        rule = EdgeCacheRule.from_dict({"path_prefix": "/api/", "ttl_seconds": 60})
        assert rule.path_prefix == "/api/"
        assert rule.ttl_seconds == 60


class TestEdgeRateLimit:
    def test_to_dict(self):
        rl = EdgeRateLimit(requests_per_second=50, burst=100, key="api_key")
        assert rl.to_dict() == {
            "requests_per_second": 50,
            "burst": 100,
            "key": "api_key",
        }

    def test_from_dict(self):
        rl = EdgeRateLimit.from_dict({"requests_per_second": 10, "burst": 20, "key": "ip"})
        assert rl.requests_per_second == 10
        assert rl.burst == 20
        assert rl.key == "ip"


class TestEdgeStatus:
    def test_from_dict(self):
        s = EdgeStatus.from_dict(EDGE_STATUS_PAYLOAD)
        assert s.edge_enabled is True
        assert s.home_pop == "se-sto1"
        assert s.cname_target == "edge.foundrydb.com"
        assert s.config_version == 3
        assert len(s.applications) == 2
        assert isinstance(s.applications[0], EdgeAppApplication)
        assert s.applications[0].zone == "se-sto1"
        assert s.applications[0].applied_version == 3
        assert s.applications[0].status == "converged"
        assert s.applications[1].zone == "fi-hel1"
        assert s.applications[1].status == "converging"

    def test_from_dict_empty_applications(self):
        s = EdgeStatus.from_dict({"edge_enabled": False, "config_version": 0})
        assert s.edge_enabled is False
        assert s.applications == []


class TestEdgeSettings:
    def test_from_dict_full(self):
        s = EdgeSettings.from_dict(EDGE_SETTINGS_PAYLOAD)
        assert s.waf_mode == "detect"
        assert s.config_version == 4
        assert s.cache_rules is not None
        assert len(s.cache_rules) == 1
        assert s.cache_rules[0].path_prefix == "/static/"
        assert s.cache_rules[0].ttl_seconds == 86400
        assert s.rate_limit is not None
        assert s.rate_limit.requests_per_second == 100
        assert s.rate_limit.key == "ip"

    def test_from_dict_no_rules_or_rate_limit(self):
        s = EdgeSettings.from_dict({"waf_mode": "off", "config_version": 1})
        assert s.waf_mode == "off"
        assert s.cache_rules is None
        assert s.rate_limit is None


# ---------------------------------------------------------------------------
# Sync EdgeAPI
# ---------------------------------------------------------------------------

class TestEdgeAPISync:
    @respx.mock
    def test_list_domains_returns_edge_domain_objects(self):
        respx.get(f"{BASE}/app-services/{APP}/domains").mock(
            return_value=httpx.Response(200, json={"domains": [DOMAIN_PAYLOAD]})
        )
        api = make_sync_api()
        domains = api.list_domains(APP)
        assert len(domains) == 1
        assert isinstance(domains[0], EdgeDomain)
        assert domains[0].id == DOMAIN_ID
        assert domains[0].domain == "shop.acme.com"

    @respx.mock
    def test_list_domains_empty(self):
        respx.get(f"{BASE}/app-services/{APP}/domains").mock(
            return_value=httpx.Response(200, json={"domains": []})
        )
        api = make_sync_api()
        assert api.list_domains(APP) == []

    @respx.mock
    def test_create_domain_sends_domain_field(self):
        route = respx.post(f"{BASE}/app-services/{APP}/domains").mock(
            return_value=httpx.Response(201, json=DOMAIN_PAYLOAD)
        )
        api = make_sync_api()
        d = api.create_domain(APP, "shop.acme.com")
        assert isinstance(d, EdgeDomain)
        assert d.status == "pending_verification"
        sent = json.loads(route.calls.last.request.content)
        assert sent == {"domain": "shop.acme.com"}

    @respx.mock
    def test_create_domain_raises_on_error(self):
        respx.post(f"{BASE}/app-services/{APP}/domains").mock(
            return_value=httpx.Response(422, json={"error": "invalid domain"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.create_domain(APP, "bad domain!")
        assert exc_info.value.status_code == 422

    @respx.mock
    def test_verify_domain_posts_and_returns_domain(self):
        route = respx.post(
            f"{BASE}/app-services/{APP}/domains/{DOMAIN_ID}/verify"
        ).mock(return_value=httpx.Response(200, json=ACTIVE_DOMAIN_PAYLOAD))
        api = make_sync_api()
        d = api.verify_domain(APP, DOMAIN_ID)
        assert isinstance(d, EdgeDomain)
        assert d.status == "active"
        assert route.called

    @respx.mock
    def test_delete_domain_succeeds(self):
        respx.delete(f"{BASE}/app-services/{APP}/domains/{DOMAIN_ID}").mock(
            return_value=httpx.Response(204, content=b"")
        )
        api = make_sync_api()
        assert api.delete_domain(APP, DOMAIN_ID) is None

    @respx.mock
    def test_delete_domain_404_is_idempotent(self):
        respx.delete(f"{BASE}/app-services/{APP}/domains/{DOMAIN_ID}").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        # Should not raise.
        assert api.delete_domain(APP, DOMAIN_ID) is None

    @respx.mock
    def test_get_status_returns_edge_status(self):
        respx.get(f"{BASE}/app-services/{APP}/edge").mock(
            return_value=httpx.Response(200, json=EDGE_STATUS_PAYLOAD)
        )
        api = make_sync_api()
        status = api.get_status(APP)
        assert isinstance(status, EdgeStatus)
        assert status.edge_enabled is True
        assert status.home_pop == "se-sto1"
        assert status.config_version == 3
        assert len(status.applications) == 2

    @respx.mock
    def test_update_settings_sends_waf_mode(self):
        route = respx.put(f"{BASE}/app-services/{APP}/edge/settings").mock(
            return_value=httpx.Response(200, json=EDGE_SETTINGS_PAYLOAD)
        )
        api = make_sync_api()
        settings = api.update_settings(APP, waf_mode="detect")
        assert isinstance(settings, EdgeSettings)
        assert settings.waf_mode == "detect"
        assert settings.config_version == 4
        sent = json.loads(route.calls.last.request.content)
        assert sent == {"waf_mode": "detect"}

    @respx.mock
    def test_update_settings_sends_cache_rules_and_rate_limit(self):
        route = respx.put(f"{BASE}/app-services/{APP}/edge/settings").mock(
            return_value=httpx.Response(200, json=EDGE_SETTINGS_PAYLOAD)
        )
        api = make_sync_api()
        api.update_settings(
            APP,
            cache_rules=[EdgeCacheRule(path_prefix="/static/", ttl_seconds=3600)],
            rate_limit=EdgeRateLimit(requests_per_second=100, burst=200, key="ip"),
            waf_mode="off",
        )
        sent = json.loads(route.calls.last.request.content)
        assert sent["cache_rules"] == [{"path_prefix": "/static/", "ttl_seconds": 3600}]
        assert sent["rate_limit"] == {
            "requests_per_second": 100,
            "burst": 200,
            "key": "ip",
        }
        assert sent["waf_mode"] == "off"

    @respx.mock
    def test_update_settings_omits_unset_fields(self):
        route = respx.put(f"{BASE}/app-services/{APP}/edge/settings").mock(
            return_value=httpx.Response(200, json=EDGE_SETTINGS_PAYLOAD)
        )
        api = make_sync_api()
        # Call with no kwargs: body should be empty.
        api.update_settings(APP)
        sent = json.loads(route.calls.last.request.content)
        assert sent == {}

    @respx.mock
    def test_update_settings_raises_on_error(self):
        respx.put(f"{BASE}/app-services/{APP}/edge/settings").mock(
            return_value=httpx.Response(400, json={"error": "invalid waf_mode"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.update_settings(APP, waf_mode="block")
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# Async AsyncEdgeAPI
# ---------------------------------------------------------------------------

class TestAsyncEdgeAPI:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_domains_returns_edge_domain_objects(self):
        respx.get(f"{BASE}/app-services/{APP}/domains").mock(
            return_value=httpx.Response(200, json={"domains": [DOMAIN_PAYLOAD]})
        )
        api = make_async_api()
        domains = await api.list_domains(APP)
        assert len(domains) == 1
        assert isinstance(domains[0], EdgeDomain)
        assert domains[0].id == DOMAIN_ID
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_domain_sends_domain_field(self):
        route = respx.post(f"{BASE}/app-services/{APP}/domains").mock(
            return_value=httpx.Response(201, json=DOMAIN_PAYLOAD)
        )
        api = make_async_api()
        d = await api.create_domain(APP, "shop.acme.com")
        assert isinstance(d, EdgeDomain)
        sent = json.loads(route.calls.last.request.content)
        assert sent == {"domain": "shop.acme.com"}
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_verify_domain_returns_domain(self):
        respx.post(
            f"{BASE}/app-services/{APP}/domains/{DOMAIN_ID}/verify"
        ).mock(return_value=httpx.Response(200, json=ACTIVE_DOMAIN_PAYLOAD))
        api = make_async_api()
        d = await api.verify_domain(APP, DOMAIN_ID)
        assert isinstance(d, EdgeDomain)
        assert d.status == "active"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_domain_succeeds(self):
        respx.delete(f"{BASE}/app-services/{APP}/domains/{DOMAIN_ID}").mock(
            return_value=httpx.Response(204, content=b"")
        )
        api = make_async_api()
        assert await api.delete_domain(APP, DOMAIN_ID) is None
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_domain_404_is_idempotent(self):
        respx.delete(f"{BASE}/app-services/{APP}/domains/{DOMAIN_ID}").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        assert await api.delete_domain(APP, DOMAIN_ID) is None
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_status_returns_edge_status(self):
        respx.get(f"{BASE}/app-services/{APP}/edge").mock(
            return_value=httpx.Response(200, json=EDGE_STATUS_PAYLOAD)
        )
        api = make_async_api()
        status = await api.get_status(APP)
        assert isinstance(status, EdgeStatus)
        assert status.edge_enabled is True
        assert len(status.applications) == 2
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_settings_sends_body(self):
        route = respx.put(f"{BASE}/app-services/{APP}/edge/settings").mock(
            return_value=httpx.Response(200, json=EDGE_SETTINGS_PAYLOAD)
        )
        api = make_async_api()
        settings = await api.update_settings(APP, waf_mode="detect")
        assert isinstance(settings, EdgeSettings)
        assert settings.waf_mode == "detect"
        sent = json.loads(route.calls.last.request.content)
        assert sent == {"waf_mode": "detect"}
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_settings_sends_cache_rules_and_rate_limit(self):
        route = respx.put(f"{BASE}/app-services/{APP}/edge/settings").mock(
            return_value=httpx.Response(200, json=EDGE_SETTINGS_PAYLOAD)
        )
        api = make_async_api()
        await api.update_settings(
            APP,
            cache_rules=[EdgeCacheRule(path_prefix="/assets/", ttl_seconds=3600)],
            rate_limit=EdgeRateLimit(requests_per_second=50, burst=100, key="api_key"),
        )
        sent = json.loads(route.calls.last.request.content)
        assert sent["cache_rules"] == [{"path_prefix": "/assets/", "ttl_seconds": 3600}]
        assert sent["rate_limit"]["key"] == "api_key"
        await api._http.aclose()
