"""
Tests for foundrydb.services - ServicesAPI (sync) and AsyncServicesAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.services import ServicesAPI, AsyncServicesAPI
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import Service, FoundryDBError

BASE = "https://api.foundrydb.test"

# Minimal service payload returned by the API.
SERVICE_PAYLOAD = {
    "id": "svc-001",
    "name": "my-pg",
    "database_type": "postgresql",
    "version": "17",
    "status": "running",
    "plan_name": "tier-2",
    "zone": "se-sto1",
    "storage_size_gb": 50,
    "storage_tier": "maxiops",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
    "dns_records": [
        {"full_domain": "svc-001.db.foundrydb.com", "record_type": "CNAME", "value": "lb.foundrydb.com"}
    ],
    "allowed_cidrs": ["0.0.0.0/0"],
    "maintenance_window": None,
}

# Helpers
def make_sync_api() -> ServicesAPI:
    return ServicesAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncServicesAPI:
    return AsyncServicesAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Sync ServicesAPI
# ---------------------------------------------------------------------------

class TestServicesAPISync:
    @respx.mock
    def test_list_returns_service_objects(self):
        respx.get(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(200, json={"services": [SERVICE_PAYLOAD]})
        )
        api = make_sync_api()
        services = api.list()
        assert len(services) == 1
        svc = services[0]
        assert isinstance(svc, Service)
        assert svc.id == "svc-001"
        assert svc.name == "my-pg"
        assert svc.database_type == "postgresql"
        assert svc.status == "running"
        assert len(svc.dns_records) == 1
        assert svc.dns_records[0].full_domain == "svc-001.db.foundrydb.com"

    @respx.mock
    def test_list_empty(self):
        respx.get(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(200, json={"services": []})
        )
        api = make_sync_api()
        assert api.list() == []

    @respx.mock
    def test_list_raises_on_server_error(self):
        respx.get(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.list()
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_get_returns_service(self):
        respx.get(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=SERVICE_PAYLOAD)
        )
        api = make_sync_api()
        svc = api.get("svc-001")
        assert isinstance(svc, Service)
        assert svc.id == "svc-001"
        assert svc.zone == "se-sto1"

    @respx.mock
    def test_get_raises_404(self):
        respx.get(f"{BASE}/managed-services/nonexistent").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.get("nonexistent")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_create_minimal_fields(self):
        respx.post(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(201, json=SERVICE_PAYLOAD)
        )
        api = make_sync_api()
        svc = api.create(
            name="my-pg",
            database_type="postgresql",
            version="17",
            plan_name="tier-2",
            zone="se-sto1",
            storage_size_gb=50,
            storage_tier="maxiops",
        )
        assert isinstance(svc, Service)
        assert svc.id == "svc-001"

    @respx.mock
    def test_create_with_all_optional_fields(self):
        route = respx.post(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(201, json=SERVICE_PAYLOAD)
        )
        api = make_sync_api()
        svc = api.create(
            name="ha-pg",
            database_type="postgresql",
            version="17",
            plan_name="tier-4",
            zone="se-sto1",
            storage_size_gb=100,
            storage_tier="maxiops",
            organization_id="org_123",
            node_count=3,
            auto_failover_enabled=True,
            replication_mode="async",
            encryption_enabled=True,
            allowed_cidrs=["10.0.0.0/8"],
            maintenance_window="sun:03:00-sun:05:00",
        )
        assert isinstance(svc, Service)
        # Org override header should have been sent.
        sent_headers = route.calls.last.request.headers
        assert sent_headers.get("x-active-org-id") == "org_123"

    @respx.mock
    def test_create_raises_on_error(self):
        respx.post(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(422, json={"error": "invalid plan"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.create(
                name="x",
                database_type="postgresql",
                version="17",
                plan_name="bad",
                zone="se-sto1",
                storage_size_gb=10,
                storage_tier="standard",
            )
        assert exc_info.value.status_code == 422

    @respx.mock
    def test_update_name(self):
        updated = dict(SERVICE_PAYLOAD, name="renamed")
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_sync_api()
        svc = api.update("svc-001", name="renamed")
        assert svc.name == "renamed"

    @respx.mock
    def test_update_multiple_fields(self):
        updated = dict(SERVICE_PAYLOAD, allowed_cidrs=["192.168.0.0/16"], plan_name="tier-4")
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_sync_api()
        svc = api.update("svc-001", allowed_cidrs=["192.168.0.0/16"], plan_name="tier-4")
        assert svc.allowed_cidrs == ["192.168.0.0/16"]

    @respx.mock
    def test_update_maintenance_window_and_storage(self):
        updated = dict(SERVICE_PAYLOAD, maintenance_window="sun:02:00", storage_size_gb=200)
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_sync_api()
        svc = api.update("svc-001", maintenance_window="sun:02:00", storage_size_gb=200)
        assert svc.maintenance_window == "sun:02:00"
        assert svc.storage_size_gb == 200

    @respx.mock
    def test_update_raises_on_error(self):
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.update("svc-001", name="x")

    @respx.mock
    def test_delete_succeeds(self):
        respx.delete(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(204, content=b"")
        )
        api = make_sync_api()
        result = api.delete("svc-001")
        assert result is None

    @respx.mock
    def test_delete_raises_on_error(self):
        respx.delete(f"{BASE}/managed-services/bad").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.delete("bad")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Async AsyncServicesAPI
# ---------------------------------------------------------------------------

class TestAsyncServicesAPI:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_returns_service_objects(self):
        respx.get(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(200, json={"services": [SERVICE_PAYLOAD]})
        )
        api = make_async_api()
        services = await api.list()
        assert len(services) == 1
        assert isinstance(services[0], Service)
        assert services[0].id == "svc-001"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_empty(self):
        respx.get(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(200, json={"services": []})
        )
        api = make_async_api()
        assert await api.list() == []
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_error(self):
        respx.get(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.list()
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_returns_service(self):
        respx.get(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=SERVICE_PAYLOAD)
        )
        api = make_async_api()
        svc = await api.get("svc-001")
        assert isinstance(svc, Service)
        assert svc.id == "svc-001"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_raises_404(self):
        respx.get(f"{BASE}/managed-services/gone").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError) as exc_info:
            await api.get("gone")
        assert exc_info.value.status_code == 404
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_minimal(self):
        respx.post(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(201, json=SERVICE_PAYLOAD)
        )
        api = make_async_api()
        svc = await api.create(
            name="my-pg",
            database_type="postgresql",
            version="17",
            plan_name="tier-2",
            zone="se-sto1",
            storage_size_gb=50,
            storage_tier="maxiops",
        )
        assert isinstance(svc, Service)
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_with_org_id(self):
        route = respx.post(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(201, json=SERVICE_PAYLOAD)
        )
        api = make_async_api()
        await api.create(
            name="ha-pg",
            database_type="postgresql",
            version="17",
            plan_name="tier-2",
            zone="se-sto1",
            storage_size_gb=50,
            storage_tier="maxiops",
            organization_id="org_abc",
            node_count=3,
        )
        sent_headers = route.calls.last.request.headers
        assert sent_headers.get("x-active-org-id") == "org_abc"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_raises_on_error(self):
        respx.post(f"{BASE}/managed-services/").mock(
            return_value=httpx.Response(422, json={"error": "invalid"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.create(
                name="x",
                database_type="postgresql",
                version="17",
                plan_name="bad",
                zone="se-sto1",
                storage_size_gb=10,
                storage_tier="standard",
            )
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_returns_service(self):
        updated = dict(SERVICE_PAYLOAD, name="new-name")
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_async_api()
        svc = await api.update("svc-001", name="new-name")
        assert svc.name == "new-name"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_storage_size(self):
        updated = dict(SERVICE_PAYLOAD, storage_size_gb=100)
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_async_api()
        svc = await api.update("svc-001", storage_size_gb=100)
        assert svc.storage_size_gb == 100
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_maintenance_window_and_cidrs(self):
        updated = dict(SERVICE_PAYLOAD, maintenance_window="sat:04:00", allowed_cidrs=["10.0.0.0/8"])
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_async_api()
        svc = await api.update("svc-001", maintenance_window="sat:04:00", allowed_cidrs=["10.0.0.0/8"])
        assert svc.maintenance_window == "sat:04:00"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_plan_name(self):
        updated = dict(SERVICE_PAYLOAD, plan_name="tier-8")
        respx.patch(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(200, json=updated)
        )
        api = make_async_api()
        svc = await api.update("svc-001", plan_name="tier-8")
        assert svc.plan_name == "tier-8"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_succeeds(self):
        respx.delete(f"{BASE}/managed-services/svc-001").mock(
            return_value=httpx.Response(204, content=b"")
        )
        api = make_async_api()
        result = await api.delete("svc-001")
        assert result is None
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_raises_on_error(self):
        respx.delete(f"{BASE}/managed-services/bad").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.delete("bad")
        await api._http.aclose()
