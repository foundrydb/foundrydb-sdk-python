"""
FoundryDB SDK - Monitoring API (sync and async).
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import ServiceMetrics, LogsTaskResponse, LogsResultResponse


class MonitoringAPI:
    """Monitoring and observability for services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_metrics(self, service_id: str) -> ServiceMetrics:
        """Get current metrics for a service."""
        data = self._http.get(f"/managed-services/{service_id}/metrics/current")
        return ServiceMetrics.from_dict(data)

    def request_logs(self, service_id: str, lines: int = 100) -> LogsTaskResponse:
        """
        Request log retrieval for a service.
        Returns a task ID. Poll :meth:`get_logs` until status is ``completed``.
        """
        data = self._http.post(f"/managed-services/{service_id}/logs?lines={lines}")
        return LogsTaskResponse.from_dict(data)

    def get_logs(self, service_id: str, task_id: str) -> LogsResultResponse:
        """Get log results for a previously requested log task."""
        data = self._http.get(
            f"/managed-services/{service_id}/logs",
            params={"task_id": task_id},
        )
        return LogsResultResponse.from_dict(data)

    def fetch_logs(
        self,
        service_id: str,
        *,
        lines: int = 100,
        timeout: float = 60.0,
        poll_interval: float = 2.0,
    ) -> str:
        """
        Convenience wrapper: request logs and poll until complete.

        :param service_id: Service UUID.
        :param lines: Number of log lines to retrieve.
        :param timeout: Maximum wait time in seconds.
        :param poll_interval: Seconds between polls.
        :returns: Log string.
        :raises TimeoutError: If logs are not ready within *timeout* seconds.
        """
        task = self.request_logs(service_id, lines)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = self.get_logs(service_id, task.task_id)
            if result.status == "completed":
                return result.logs
            time.sleep(poll_interval)
        raise TimeoutError(
            f"Log retrieval timed out after {timeout}s (task {task.task_id})"
        )


class AsyncMonitoringAPI:
    """Monitoring and observability for services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_metrics(self, service_id: str) -> ServiceMetrics:
        """Get current metrics for a service."""
        data = await self._http.get(f"/managed-services/{service_id}/metrics/current")
        return ServiceMetrics.from_dict(data)

    async def request_logs(self, service_id: str, lines: int = 100) -> LogsTaskResponse:
        """Request log retrieval for a service (returns a task ID)."""
        data = await self._http.post(f"/managed-services/{service_id}/logs?lines={lines}")
        return LogsTaskResponse.from_dict(data)

    async def get_logs(self, service_id: str, task_id: str) -> LogsResultResponse:
        """Get log results for a previously requested log task."""
        data = await self._http.get(
            f"/managed-services/{service_id}/logs",
            params={"task_id": task_id},
        )
        return LogsResultResponse.from_dict(data)

    async def fetch_logs(
        self,
        service_id: str,
        *,
        lines: int = 100,
        timeout: float = 60.0,
        poll_interval: float = 2.0,
    ) -> str:
        """
        Convenience wrapper: request logs and poll until complete.

        :raises TimeoutError: If logs are not ready within *timeout* seconds.
        """
        task = await self.request_logs(service_id, lines)
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            result = await self.get_logs(service_id, task.task_id)
            if result.status == "completed":
                return result.logs
            await asyncio.sleep(poll_interval)
        raise TimeoutError(
            f"Log retrieval timed out after {timeout}s (task {task.task_id})"
        )
