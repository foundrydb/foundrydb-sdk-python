"""
Tests for foundrydb.backups - BackupsAPI (sync) and AsyncBackupsAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.backups import BackupsAPI, AsyncBackupsAPI
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import Backup, TriggerBackupResponse, FoundryDBError

BASE = "https://api.foundrydb.test"
SVC = "svc-001"

BACKUP_PAYLOAD = {
    "id": "bkp-001",
    "service_id": SVC,
    "status": "completed",
    "backup_type": "full",
    "size_bytes": 1048576,
    "created_at": "2026-01-01T02:00:00Z",
    "completed_at": "2026-01-01T02:05:00Z",
    "error_message": None,
}

TRIGGER_PAYLOAD = {
    "backup_id": "bkp-002",
}


def make_sync_api() -> BackupsAPI:
    return BackupsAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncBackupsAPI:
    return AsyncBackupsAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Sync BackupsAPI
# ---------------------------------------------------------------------------

class TestBackupsAPISync:
    @respx.mock
    def test_list_returns_backup_objects(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [BACKUP_PAYLOAD]})
        )
        api = make_sync_api()
        backups = api.list(SVC)
        assert len(backups) == 1
        assert isinstance(backups[0], Backup)
        assert backups[0].id == "bkp-001"

    @respx.mock
    def test_list_backup_fields(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [BACKUP_PAYLOAD]})
        )
        api = make_sync_api()
        bkp = api.list(SVC)[0]
        assert bkp.service_id == SVC
        assert bkp.status == "completed"
        assert bkp.backup_type == "full"
        assert bkp.size_bytes == 1048576
        assert bkp.created_at == "2026-01-01T02:00:00Z"
        assert bkp.completed_at == "2026-01-01T02:05:00Z"
        assert bkp.error_message is None

    @respx.mock
    def test_list_backup_with_error_message(self):
        failed = dict(BACKUP_PAYLOAD, status="failed", error_message="disk full", completed_at=None)
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [failed]})
        )
        api = make_sync_api()
        bkp = api.list(SVC)[0]
        assert bkp.status == "failed"
        assert bkp.error_message == "disk full"
        assert bkp.completed_at is None

    @respx.mock
    def test_list_backup_nullable_size(self):
        no_size = dict(BACKUP_PAYLOAD, size_bytes=None)
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [no_size]})
        )
        api = make_sync_api()
        bkp = api.list(SVC)[0]
        assert bkp.size_bytes is None

    @respx.mock
    def test_list_empty(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": []})
        )
        api = make_sync_api()
        assert api.list(SVC) == []

    @respx.mock
    def test_list_multiple_backups(self):
        bkp2 = dict(BACKUP_PAYLOAD, id="bkp-002")
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [BACKUP_PAYLOAD, bkp2]})
        )
        api = make_sync_api()
        backups = api.list(SVC)
        assert len(backups) == 2

    @respx.mock
    def test_list_raises_on_404(self):
        respx.get(f"{BASE}/managed-services/bad/backups").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.list("bad")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_list_raises_on_500(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.list(SVC)

    @respx.mock
    def test_trigger_returns_response(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json=TRIGGER_PAYLOAD)
        )
        api = make_sync_api()
        resp = api.trigger(SVC)
        assert isinstance(resp, TriggerBackupResponse)
        assert resp.backup_id == "bkp-002"

    @respx.mock
    def test_trigger_raw_field(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json=TRIGGER_PAYLOAD)
        )
        api = make_sync_api()
        resp = api.trigger(SVC)
        assert resp.raw == TRIGGER_PAYLOAD

    @respx.mock
    def test_trigger_empty_response(self):
        """Some implementations return 204 with no body; SDK handles None gracefully."""
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(204, content=b"")
        )
        api = make_sync_api()
        resp = api.trigger(SVC)
        assert isinstance(resp, TriggerBackupResponse)
        assert resp.backup_id is None

    @respx.mock
    def test_trigger_raises_on_409(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(409, json={"error": "backup already running"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.trigger(SVC)
        assert exc_info.value.status_code == 409

    @respx.mock
    def test_trigger_raises_on_500(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(500, json={"error": "internal"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.trigger(SVC)

    @respx.mock
    def test_list_raw_field_populated(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [BACKUP_PAYLOAD]})
        )
        api = make_sync_api()
        bkp = api.list(SVC)[0]
        assert bkp.raw == BACKUP_PAYLOAD


# ---------------------------------------------------------------------------
# Async AsyncBackupsAPI
# ---------------------------------------------------------------------------

class TestAsyncBackupsAPI:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_returns_backup_objects(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [BACKUP_PAYLOAD]})
        )
        api = make_async_api()
        backups = await api.list(SVC)
        assert len(backups) == 1
        assert isinstance(backups[0], Backup)
        assert backups[0].id == "bkp-001"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_empty(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": []})
        )
        api = make_async_api()
        assert await api.list(SVC) == []
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_backup_fields(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json={"backups": [BACKUP_PAYLOAD]})
        )
        api = make_async_api()
        bkp = (await api.list(SVC))[0]
        assert bkp.status == "completed"
        assert bkp.size_bytes == 1048576
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_404(self):
        respx.get(f"{BASE}/managed-services/bad/backups").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError) as exc_info:
            await api.list("bad")
        assert exc_info.value.status_code == 404
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_500(self):
        respx.get(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.list(SVC)
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_trigger_returns_response(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(200, json=TRIGGER_PAYLOAD)
        )
        api = make_async_api()
        resp = await api.trigger(SVC)
        assert isinstance(resp, TriggerBackupResponse)
        assert resp.backup_id == "bkp-002"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_trigger_empty_response(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(204, content=b"")
        )
        api = make_async_api()
        resp = await api.trigger(SVC)
        assert isinstance(resp, TriggerBackupResponse)
        assert resp.backup_id is None
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_trigger_raises_on_409(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(409, json={"error": "conflict"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError) as exc_info:
            await api.trigger(SVC)
        assert exc_info.value.status_code == 409
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_trigger_raises_on_500(self):
        respx.post(f"{BASE}/managed-services/{SVC}/backups").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.trigger(SVC)
        await api._http.aclose()
