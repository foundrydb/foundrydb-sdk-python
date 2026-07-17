"""
Tests for foundrydb.inference_services - InferenceServicesAPI (sync) and
AsyncInferenceServicesAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.inference_services import (
    InferenceServicesAPI,
    AsyncInferenceServicesAPI,
)
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import InferenceModelAdapter, FoundryDBError

BASE = "https://api.foundrydb.test"
SVC = "svc-001"
ADP = "adp-001"

ADAPTER_UPLOADED = {
    "id": ADP,
    "organization_id": "org-1",
    "inference_service_id": None,
    "base_model_id": "mistral-small",
    "served_model_name": "support-bot",
    "version": 3,
    "files_bucket": "org-1-adapters",
    "files_key_prefix": "support-bot/v3",
    "adapter_sha256": "a" * 64,
    "size_bytes": 104857600,
    "base_model_license": "apache-2.0",
    "status": "uploaded",
    "created_at": "2026-07-17T00:00:00Z",
    "promoted_at": None,
}

ADAPTER_ACTIVE = {
    **ADAPTER_UPLOADED,
    "id": "adp-002",
    "inference_service_id": SVC,
    "version": 2,
    "status": "active",
    "promoted_at": "2026-07-17T02:00:00Z",
}

REGISTER_KWARGS = dict(
    base_model_id="mistral-small",
    served_model_name="support-bot",
    version=3,
    files_bucket="org-1-adapters",
    files_key_prefix="support-bot/v3",
    adapter_sha256="a" * 64,
    size_bytes=104857600,
    base_model_license="apache-2.0",
)


def make_sync_api() -> InferenceServicesAPI:
    return InferenceServicesAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncInferenceServicesAPI:
    return AsyncInferenceServicesAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class TestInferenceServicesAPISync:
    @respx.mock
    def test_register_adapter_posts_body_and_returns_adapter(self):
        route = respx.post(f"{BASE}/inference-services/adapters").mock(
            return_value=httpx.Response(201, json={"adapter": ADAPTER_UPLOADED})
        )
        adapter = make_sync_api().register_adapter(**REGISTER_KWARGS)

        assert route.called
        body = route.calls.last.request.content.decode()
        assert '"base_model_id": "mistral-small"' in body
        assert '"served_model_name": "support-bot"' in body
        assert '"adapter_sha256"' in body
        assert '"size_bytes": 104857600' in body

        assert isinstance(adapter, InferenceModelAdapter)
        assert adapter.id == ADP
        assert adapter.status == "uploaded"
        assert adapter.inference_service_id is None
        assert adapter.version == 3
        assert adapter.promoted_at is None

    @respx.mock
    def test_register_adapter_sends_org_header_and_body(self):
        route = respx.post(f"{BASE}/inference-services/adapters").mock(
            return_value=httpx.Response(201, json={"adapter": ADAPTER_UPLOADED})
        )
        make_sync_api().register_adapter(organization_id="org-99", **REGISTER_KWARGS)

        req = route.calls.last.request
        assert req.headers.get("X-Active-Org-ID") == "org-99"
        assert '"organization_id": "org-99"' in req.content.decode()

    @respx.mock
    def test_register_adapter_raises_on_409(self):
        respx.post(f"{BASE}/inference-services/adapters").mock(
            return_value=httpx.Response(409, json={"error": "already registered"})
        )
        with pytest.raises(FoundryDBError):
            make_sync_api().register_adapter(**REGISTER_KWARGS)

    @respx.mock
    def test_list_adapters_returns_bound_and_uploaded(self):
        respx.get(f"{BASE}/inference-services/{SVC}/adapters").mock(
            return_value=httpx.Response(
                200, json={"adapters": [ADAPTER_UPLOADED, ADAPTER_ACTIVE]}
            )
        )
        adapters = make_sync_api().list_adapters(SVC)

        assert len(adapters) == 2
        assert adapters[0].status == "uploaded"
        assert adapters[0].inference_service_id is None
        assert adapters[1].status == "active"
        assert adapters[1].inference_service_id == SVC

    @respx.mock
    def test_list_adapters_empty(self):
        respx.get(f"{BASE}/inference-services/{SVC}/adapters").mock(
            return_value=httpx.Response(200, json={"adapters": []})
        )
        assert make_sync_api().list_adapters(SVC) == []

    @respx.mock
    def test_list_adapters_raises_on_404(self):
        respx.get(f"{BASE}/inference-services/missing/adapters").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        with pytest.raises(FoundryDBError):
            make_sync_api().list_adapters("missing")

    @respx.mock
    def test_promote_adapter_returns_active(self):
        route = respx.post(
            f"{BASE}/inference-services/{SVC}/adapters/{ADP}/promote"
        ).mock(return_value=httpx.Response(200, json={"adapter": ADAPTER_ACTIVE}))
        adapter = make_sync_api().promote_adapter(SVC, ADP)

        assert route.called
        assert adapter.status == "active"
        assert adapter.inference_service_id == SVC
        assert adapter.promoted_at == "2026-07-17T02:00:00Z"

    @respx.mock
    def test_promote_adapter_raises_on_400(self):
        respx.post(
            f"{BASE}/inference-services/{SVC}/adapters/{ADP}/promote"
        ).mock(return_value=httpx.Response(400, json={"error": "base model mismatch"}))
        with pytest.raises(FoundryDBError):
            make_sync_api().promote_adapter(SVC, ADP)


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class TestInferenceServicesAPIAsync:
    @pytest.mark.asyncio
    @respx.mock
    async def test_register_adapter(self):
        respx.post(f"{BASE}/inference-services/adapters").mock(
            return_value=httpx.Response(201, json={"adapter": ADAPTER_UPLOADED})
        )
        adapter = await make_async_api().register_adapter(**REGISTER_KWARGS)
        assert adapter.id == ADP
        assert adapter.status == "uploaded"

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_adapters(self):
        respx.get(f"{BASE}/inference-services/{SVC}/adapters").mock(
            return_value=httpx.Response(
                200, json={"adapters": [ADAPTER_UPLOADED, ADAPTER_ACTIVE]}
            )
        )
        adapters = await make_async_api().list_adapters(SVC)
        assert [a.status for a in adapters] == ["uploaded", "active"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_promote_adapter(self):
        respx.post(
            f"{BASE}/inference-services/{SVC}/adapters/{ADP}/promote"
        ).mock(return_value=httpx.Response(200, json={"adapter": ADAPTER_ACTIVE}))
        adapter = await make_async_api().promote_adapter(SVC, ADP)
        assert adapter.status == "active"
        assert adapter.inference_service_id == SVC
