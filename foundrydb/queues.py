"""
FoundryDB SDK - Queues API (sync and async).

Message queues are hosted on PostgreSQL managed services. The durable state
(messages) lives in the customer's database, transactional with their data.
The controller brokers data-plane operations (enqueue, stats) to the agent
on the database VM.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    Queue,
    QueueEnqueueResult,
    QueueStatsResult,
)


class QueuesAPI:
    """Manages message queues on PostgreSQL services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        service_id: str,
        *,
        name: str,
        database_name: str = "",
        visibility_timeout_seconds: Optional[int] = None,
        max_attempts: Optional[int] = None,
        dlq_enabled: Optional[bool] = None,
    ) -> Queue:
        """Create a queue on a PostgreSQL managed service.

        Provisioning is asynchronous: the returned queue starts in the
        Provisioning status. Poll :meth:`get` until it reaches Active. A
        service supports up to 50 queues.

        Args:
            service_id: ID of the PostgreSQL managed service.
            name: Queue name, unique within the service.
            database_name: Database within the service to host the queue.
                Defaults to ``defaultdb``.
            visibility_timeout_seconds: Redelivery horizon in seconds.
                Defaults to 30.
            max_attempts: How many deliveries before a message is dead-lettered
                or dropped. Defaults to 5.
            dlq_enabled: Whether to use a dead-letter queue. Defaults to True.
        """
        body: Dict[str, Any] = {"name": name}
        if database_name:
            body["database_name"] = database_name
        if visibility_timeout_seconds is not None:
            body["visibility_timeout_seconds"] = visibility_timeout_seconds
        if max_attempts is not None:
            body["max_attempts"] = max_attempts
        if dlq_enabled is not None:
            body["dlq_enabled"] = dlq_enabled
        data = self._http.post(f"/managed-services/{service_id}/queues", body)
        return Queue.from_dict(data)

    def list(self, service_id: str) -> List[Queue]:
        """Return the queues of a service, each reconciled against its
        provisioning task."""
        data = self._http.get(f"/managed-services/{service_id}/queues")
        return [Queue.from_dict(q) for q in data.get("queues", [])]

    def get(self, service_id: str, queue_name: str) -> Optional[Queue]:
        """Return one queue by name, or ``None`` when not found."""
        try:
            data = self._http.get(f"/managed-services/{service_id}/queues/{queue_name}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return Queue.from_dict(data)

    def delete(self, service_id: str, queue_name: str) -> Optional[Queue]:
        """Schedule asynchronous removal of a queue.

        Returns the queue in the Deprovisioning status (202). The row
        disappears from :meth:`list` once the agent confirms deletion.
        Returns ``None`` when the queue does not exist (idempotent).
        """
        raw = self._http.delete(f"/managed-services/{service_id}/queues/{queue_name}")
        return Queue.from_dict(raw) if raw else None

    def enqueue(
        self,
        service_id: str,
        queue_name: str,
        messages: List[Dict[str, Any]],
    ) -> str:
        """Write a batch of messages to an Active queue.

        The batch lands in one transaction, all-or-nothing. Returns the task
        ID to poll with :meth:`get_enqueue_result` (202).

        Args:
            service_id: ID of the PostgreSQL managed service.
            queue_name: Name of the target queue.
            messages: List of message dicts, each with ``payload`` (arbitrary
                JSON dict) and optional ``delay_seconds`` (default 0).
        """
        body: Dict[str, Any] = {"messages": messages}
        data = self._http.post(
            f"/managed-services/{service_id}/queues/{queue_name}/messages", body
        )
        return data.get("task_id", "") if data else ""

    def get_enqueue_result(
        self, service_id: str, queue_name: str, task_id: str
    ) -> QueueEnqueueResult:
        """Poll an enqueue task. ``result.message_ids`` is set once
        COMPLETED."""
        data = self._http.get(
            f"/managed-services/{service_id}/queues/{queue_name}/messages",
            params={"task_id": task_id},
        )
        return QueueEnqueueResult.from_dict(data)

    def request_stats(self, service_id: str, queue_name: str) -> str:
        """Create a depth-snapshot task for an Active queue.

        Returns the task ID to poll with :meth:`get_stats`.
        """
        data = self._http.post(
            f"/managed-services/{service_id}/queues/{queue_name}/stats"
        )
        return data.get("task_id", "") if data else ""

    def get_stats(
        self, service_id: str, queue_name: str, task_id: str
    ) -> QueueStatsResult:
        """Poll a stats task. ``result`` is set once COMPLETED."""
        data = self._http.get(
            f"/managed-services/{service_id}/queues/{queue_name}/stats",
            params={"task_id": task_id},
        )
        return QueueStatsResult.from_dict(data)


class AsyncQueuesAPI:
    """Manages message queues on PostgreSQL services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        service_id: str,
        *,
        name: str,
        database_name: str = "",
        visibility_timeout_seconds: Optional[int] = None,
        max_attempts: Optional[int] = None,
        dlq_enabled: Optional[bool] = None,
    ) -> Queue:
        """Create a queue on a PostgreSQL managed service."""
        body: Dict[str, Any] = {"name": name}
        if database_name:
            body["database_name"] = database_name
        if visibility_timeout_seconds is not None:
            body["visibility_timeout_seconds"] = visibility_timeout_seconds
        if max_attempts is not None:
            body["max_attempts"] = max_attempts
        if dlq_enabled is not None:
            body["dlq_enabled"] = dlq_enabled
        data = await self._http.post(
            f"/managed-services/{service_id}/queues", body
        )
        return Queue.from_dict(data)

    async def list(self, service_id: str) -> List[Queue]:
        """Return the queues of a service."""
        data = await self._http.get(f"/managed-services/{service_id}/queues")
        return [Queue.from_dict(q) for q in data.get("queues", [])]

    async def get(self, service_id: str, queue_name: str) -> Optional[Queue]:
        """Return one queue by name, or ``None`` when not found."""
        try:
            data = await self._http.get(
                f"/managed-services/{service_id}/queues/{queue_name}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return Queue.from_dict(data)

    async def delete(self, service_id: str, queue_name: str) -> Optional[Queue]:
        """Schedule asynchronous removal of a queue (idempotent)."""
        raw = await self._http.delete(
            f"/managed-services/{service_id}/queues/{queue_name}"
        )
        return Queue.from_dict(raw) if raw else None

    async def enqueue(
        self,
        service_id: str,
        queue_name: str,
        messages: List[Dict[str, Any]],
    ) -> str:
        """Write a batch of messages to an Active queue. Returns the task ID."""
        body: Dict[str, Any] = {"messages": messages}
        data = await self._http.post(
            f"/managed-services/{service_id}/queues/{queue_name}/messages", body
        )
        return data.get("task_id", "") if data else ""

    async def get_enqueue_result(
        self, service_id: str, queue_name: str, task_id: str
    ) -> QueueEnqueueResult:
        """Poll an enqueue task."""
        data = await self._http.get(
            f"/managed-services/{service_id}/queues/{queue_name}/messages",
            params={"task_id": task_id},
        )
        return QueueEnqueueResult.from_dict(data)

    async def request_stats(self, service_id: str, queue_name: str) -> str:
        """Create a depth-snapshot task. Returns the task ID."""
        data = await self._http.post(
            f"/managed-services/{service_id}/queues/{queue_name}/stats"
        )
        return data.get("task_id", "") if data else ""

    async def get_stats(
        self, service_id: str, queue_name: str, task_id: str
    ) -> QueueStatsResult:
        """Poll a stats task."""
        data = await self._http.get(
            f"/managed-services/{service_id}/queues/{queue_name}/stats",
            params={"task_id": task_id},
        )
        return QueueStatsResult.from_dict(data)
