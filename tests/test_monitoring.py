"""
Tests for foundrydb.monitoring - MonitoringAPI (sync) and AsyncMonitoringAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.monitoring import MonitoringAPI, AsyncMonitoringAPI
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import ServiceMetrics, LogsTaskResponse, LogsResultResponse, FoundryDBError

BASE = "https://api.foundrydb.test"
SVC = "svc-001"

METRICS_PAYLOAD = {
    "cpu_usage_percent": 12.5,
    "memory_usage_percent": 45.0,
    "disk_usage_percent": 22.0,
    "connections_active": 10,
    "connections_max": 100,
    "replication_lag_ms": 0.0,
    "queries_per_second": 55.3,
}

LOGS_TASK_PAYLOAD = {"task_id": "task-abc"}

LOGS_RESULT_COMPLETED = {"status": "completed", "logs": "INFO: database started\nINFO: ready"}
LOGS_RESULT_PENDING = {"status": "pending", "logs": ""}


def make_sync_api() -> MonitoringAPI:
    return MonitoringAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncMonitoringAPI:
    return AsyncMonitoringAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Sync MonitoringAPI
# ---------------------------------------------------------------------------

class TestMonitoringAPISync:
    @respx.mock
    def test_get_metrics_returns_object(self):
        respx.get(f"{BASE}/managed-services/{SVC}/metrics/current").mock(
            return_value=httpx.Response(200, json=METRICS_PAYLOAD)
        )
        api = make_sync_api()
        metrics = api.get_metrics(SVC)
        assert isinstance(metrics, ServiceMetrics)
        assert metrics.cpu_usage_percent == 12.5
        assert metrics.memory_usage_percent == 45.0
        assert metrics.disk_usage_percent == 22.0
        assert metrics.connections_active == 10
        assert metrics.connections_max == 100
        assert metrics.replication_lag_ms == 0.0
        assert metrics.queries_per_second == 55.3

    @respx.mock
    def test_get_metrics_nullable_fields(self):
        sparse = {k: None for k in METRICS_PAYLOAD}
        respx.get(f"{BASE}/managed-services/{SVC}/metrics/current").mock(
            return_value=httpx.Response(200, json=sparse)
        )
        api = make_sync_api()
        metrics = api.get_metrics(SVC)
        assert metrics.cpu_usage_percent is None
        assert metrics.connections_active is None

    @respx.mock
    def test_get_metrics_raises_on_404(self):
        respx.get(f"{BASE}/managed-services/bad/metrics/current").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.get_metrics("bad")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_get_metrics_raises_on_500(self):
        respx.get(f"{BASE}/managed-services/{SVC}/metrics/current").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.get_metrics(SVC)

    @respx.mock
    def test_get_metrics_raw_field(self):
        respx.get(f"{BASE}/managed-services/{SVC}/metrics/current").mock(
            return_value=httpx.Response(200, json=METRICS_PAYLOAD)
        )
        api = make_sync_api()
        metrics = api.get_metrics(SVC)
        assert metrics.raw == METRICS_PAYLOAD

    @respx.mock
    def test_request_logs_returns_task(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        api = make_sync_api()
        task = api.request_logs(SVC)
        assert isinstance(task, LogsTaskResponse)
        assert task.task_id == "task-abc"

    @respx.mock
    def test_request_logs_custom_lines(self):
        route = respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=200").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        api = make_sync_api()
        api.request_logs(SVC, lines=200)
        assert route.called

    @respx.mock
    def test_request_logs_raises_on_error(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.request_logs(SVC)

    @respx.mock
    def test_get_logs_returns_result(self):
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_COMPLETED)
        )
        api = make_sync_api()
        result = api.get_logs(SVC, "task-abc")
        assert isinstance(result, LogsResultResponse)
        assert result.status == "completed"
        assert "database started" in result.logs

    @respx.mock
    def test_get_logs_pending(self):
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_PENDING)
        )
        api = make_sync_api()
        result = api.get_logs(SVC, "task-abc")
        assert result.status == "pending"
        assert result.logs == ""

    @respx.mock
    def test_get_logs_raises_on_error(self):
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(404, json={"error": "task not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.get_logs(SVC, "bad-task")

    @respx.mock
    def test_fetch_logs_completes_immediately(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_COMPLETED)
        )
        api = make_sync_api()
        logs = api.fetch_logs(SVC)
        assert "database started" in logs

    @respx.mock
    def test_fetch_logs_polls_until_complete(self):
        """First poll returns pending, second returns completed."""
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=50").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        # Side effects: first call pending, second call completed.
        call_count = {"n": 0}
        def get_side_effect(request):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return httpx.Response(200, json=LOGS_RESULT_PENDING)
            return httpx.Response(200, json=LOGS_RESULT_COMPLETED)

        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(side_effect=get_side_effect)
        api = make_sync_api()
        logs = api.fetch_logs(SVC, lines=50, poll_interval=0.01)
        assert "database started" in logs
        assert call_count["n"] == 2

    @respx.mock
    def test_fetch_logs_raises_timeout(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_PENDING)
        )
        api = make_sync_api()
        with pytest.raises(TimeoutError) as exc_info:
            api.fetch_logs(SVC, timeout=0.01, poll_interval=0.001)
        assert "task-abc" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Async AsyncMonitoringAPI
# ---------------------------------------------------------------------------

class TestAsyncMonitoringAPI:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_metrics_returns_object(self):
        respx.get(f"{BASE}/managed-services/{SVC}/metrics/current").mock(
            return_value=httpx.Response(200, json=METRICS_PAYLOAD)
        )
        api = make_async_api()
        metrics = await api.get_metrics(SVC)
        assert isinstance(metrics, ServiceMetrics)
        assert metrics.cpu_usage_percent == 12.5
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_metrics_nullable_fields(self):
        sparse = {k: None for k in METRICS_PAYLOAD}
        respx.get(f"{BASE}/managed-services/{SVC}/metrics/current").mock(
            return_value=httpx.Response(200, json=sparse)
        )
        api = make_async_api()
        metrics = await api.get_metrics(SVC)
        assert metrics.cpu_usage_percent is None
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_metrics_raises_on_404(self):
        respx.get(f"{BASE}/managed-services/bad/metrics/current").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.get_metrics("bad")
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_request_logs_returns_task(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        api = make_async_api()
        task = await api.request_logs(SVC)
        assert isinstance(task, LogsTaskResponse)
        assert task.task_id == "task-abc"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_request_logs_custom_lines(self):
        route = respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=500").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        api = make_async_api()
        await api.request_logs(SVC, lines=500)
        assert route.called
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_request_logs_raises_on_error(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.request_logs(SVC)
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_logs_returns_result(self):
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_COMPLETED)
        )
        api = make_async_api()
        result = await api.get_logs(SVC, "task-abc")
        assert isinstance(result, LogsResultResponse)
        assert result.status == "completed"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_logs_raises_on_error(self):
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.get_logs(SVC, "bad")
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_logs_completes_immediately(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_COMPLETED)
        )
        api = make_async_api()
        logs = await api.fetch_logs(SVC)
        assert "database started" in logs
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_logs_polls_until_complete(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        call_count = {"n": 0}
        def get_side_effect(request):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return httpx.Response(200, json=LOGS_RESULT_PENDING)
            return httpx.Response(200, json=LOGS_RESULT_COMPLETED)

        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(side_effect=get_side_effect)
        api = make_async_api()
        logs = await api.fetch_logs(SVC, poll_interval=0.01)
        assert "database started" in logs
        assert call_count["n"] == 2
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_logs_raises_timeout(self):
        respx.post(f"{BASE}/managed-services/{SVC}/logs?lines=100").mock(
            return_value=httpx.Response(200, json=LOGS_TASK_PAYLOAD)
        )
        respx.get(f"{BASE}/managed-services/{SVC}/logs").mock(
            return_value=httpx.Response(200, json=LOGS_RESULT_PENDING)
        )
        api = make_async_api()
        with pytest.raises(TimeoutError) as exc_info:
            await api.fetch_logs(SVC, timeout=0.01, poll_interval=0.001)
        assert "task-abc" in str(exc_info.value)
        await api._http.aclose()
