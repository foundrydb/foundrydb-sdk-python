"""
FoundryDB SDK - App Jobs API (sync and async).

App jobs are container runs (image, command, and environment layered over the
app's own configuration) with an optional cron schedule. A job without a
schedule only runs when triggered explicitly via run(). Each invocation is
tracked end-to-end with status, exit code, and log capture.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    AppJob,
    AppJobInvocation,
    AppJobInvocationLogs,
)


class AppJobsAPI:
    """Manages app jobs for a FoundryDB app service (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Job definitions
    # ------------------------------------------------------------------

    def create(
        self,
        app_service_id: str,
        *,
        name: str,
        schedule_cron: Optional[str] = None,
        timezone: str = "UTC",
        enabled: Optional[bool] = None,
        image_ref: Optional[str] = None,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        retry_backoff_seconds: Optional[int] = None,
        max_runtime_seconds: Optional[int] = None,
        concurrency_cap: Optional[int] = None,
    ) -> AppJob:
        """Create a job definition on an app service.

        A service supports up to 20 jobs. Creating a second job with the same
        name returns a conflict. Nil optional fields take the platform defaults
        (enabled, UTC, no retries, 1 hour max runtime, concurrency cap 1).

        Args:
            app_service_id: ID of the app service.
            name: Job name, unique within the service.
            schedule_cron: Five-field cron expression or descriptor (e.g.
                ``@daily``). ``None`` means manual-only.
            timezone: IANA timezone for the cron schedule. Defaults to UTC.
            enabled: Whether the job schedule is active. Defaults to True.
            image_ref: Container image override. ``None`` inherits the app's
                image.
            command: Container argv override (exec form). ``None`` uses the
                image's default command.
            env: Extra environment variables layered over the app's env.
            max_retries: Number of automatic retries on failure.
            retry_backoff_seconds: Seconds between retry attempts.
            max_runtime_seconds: Wall-clock timeout per invocation.
            concurrency_cap: Maximum simultaneous invocations.
        """
        body: Dict[str, Any] = {"name": name}
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if timezone:
            body["timezone"] = timezone
        if enabled is not None:
            body["enabled"] = enabled
        if image_ref is not None:
            body["image_ref"] = image_ref
        if command is not None:
            body["command"] = command
        if env is not None:
            body["env"] = env
        if max_retries is not None:
            body["max_retries"] = max_retries
        if retry_backoff_seconds is not None:
            body["retry_backoff_seconds"] = retry_backoff_seconds
        if max_runtime_seconds is not None:
            body["max_runtime_seconds"] = max_runtime_seconds
        if concurrency_cap is not None:
            body["concurrency_cap"] = concurrency_cap
        data = self._http.post(f"/app-services/{app_service_id}/jobs", body)
        return AppJob.from_dict(data)

    def list(self, app_service_id: str) -> List[AppJob]:
        """Return the job definitions of an app service, oldest first."""
        data = self._http.get(f"/app-services/{app_service_id}/jobs")
        return [AppJob.from_dict(j) for j in data.get("jobs", [])]

    def get(self, app_service_id: str, job_id: str) -> Optional[AppJob]:
        """Return one job definition, or ``None`` when not found."""
        try:
            data = self._http.get(f"/app-services/{app_service_id}/jobs/{job_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return AppJob.from_dict(data)

    def update(
        self,
        app_service_id: str,
        job_id: str,
        *,
        schedule_cron: Optional[str] = None,
        clear_schedule: bool = False,
        timezone: Optional[str] = None,
        enabled: Optional[bool] = None,
        image_ref: Optional[str] = None,
        clear_image_ref: bool = False,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        retry_backoff_seconds: Optional[int] = None,
        max_runtime_seconds: Optional[int] = None,
        concurrency_cap: Optional[int] = None,
    ) -> AppJob:
        """Apply a partial update to a job definition.

        Unset fields keep their current value. ``clear_schedule=True`` removes
        the cron schedule; ``clear_image_ref=True`` removes the image
        override so the job inherits the app's image again.
        """
        body: Dict[str, Any] = {}
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if clear_schedule:
            body["clear_schedule"] = True
        if timezone is not None:
            body["timezone"] = timezone
        if enabled is not None:
            body["enabled"] = enabled
        if image_ref is not None:
            body["image_ref"] = image_ref
        if clear_image_ref:
            body["clear_image_ref"] = True
        if command is not None:
            body["command"] = command
        if env is not None:
            body["env"] = env
        if max_retries is not None:
            body["max_retries"] = max_retries
        if retry_backoff_seconds is not None:
            body["retry_backoff_seconds"] = retry_backoff_seconds
        if max_runtime_seconds is not None:
            body["max_runtime_seconds"] = max_runtime_seconds
        if concurrency_cap is not None:
            body["concurrency_cap"] = concurrency_cap
        data = self._http.patch(f"/app-services/{app_service_id}/jobs/{job_id}", body)
        return AppJob.from_dict(data)

    def delete(self, app_service_id: str, job_id: str) -> None:
        """Delete a job definition and its invocation history.

        A running invocation finishes on the VM but reports into the deleted
        history. Idempotent (404 treated as success).
        """
        try:
            self._http.delete(f"/app-services/{app_service_id}/jobs/{job_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return
            raise

    # ------------------------------------------------------------------
    # Invocations
    # ------------------------------------------------------------------

    def run(self, app_service_id: str, job_id: str) -> AppJobInvocation:
        """Trigger a manual invocation and return the queued invocation (202).

        When the job is at its concurrency cap the API returns a conflict
        (409); retry once a slot frees. Execution is asynchronous: poll
        :meth:`get_invocation` until the status is terminal.
        """
        data = self._http.post(
            f"/app-services/{app_service_id}/jobs/{job_id}/run"
        )
        return AppJobInvocation.from_dict(data)

    def list_invocations(
        self,
        app_service_id: str,
        job_id: str,
        *,
        limit: int = 0,
        offset: int = 0,
    ) -> List[AppJobInvocation]:
        """Return the invocation history of a job, newest first.

        Args:
            app_service_id: ID of the app service.
            job_id: ID of the job.
            limit: Page size cap (server default 50, max 200). Pass 0 for the
                server default.
            offset: Number of rows to skip.
        """
        params: Dict[str, Any] = {}
        if limit > 0:
            params["limit"] = limit
        if offset > 0:
            params["offset"] = offset
        data = self._http.get(
            f"/app-services/{app_service_id}/jobs/{job_id}/invocations",
            params=params or None,
        )
        return [AppJobInvocation.from_dict(i) for i in data.get("invocations", [])]

    def get_invocation(
        self, app_service_id: str, job_id: str, invocation_id: str
    ) -> Optional[AppJobInvocation]:
        """Return one invocation, or ``None`` when not found."""
        try:
            data = self._http.get(
                f"/app-services/{app_service_id}/jobs/{job_id}/invocations/{invocation_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return AppJobInvocation.from_dict(data)

    def request_invocation_logs(
        self,
        app_service_id: str,
        job_id: str,
        invocation_id: str,
        *,
        lines: int = 0,
    ) -> str:
        """Ask the agent to fetch the logs of one invocation.

        Returns the task ID to poll with :meth:`get_invocation_logs`. Invocations
        that never ran (skips) have no logs and return a bad request.

        Args:
            app_service_id: ID of the app service.
            job_id: ID of the job.
            invocation_id: ID of the invocation.
            lines: Number of tail lines to capture (server default 200,
                max 1000). Pass 0 for the server default.
        """
        path = f"/app-services/{app_service_id}/jobs/{job_id}/invocations/{invocation_id}/logs"
        params: Dict[str, Any] = {}
        if lines > 0:
            params["lines"] = lines
        data = self._http.post(path, params or None)
        return data.get("task_id", "") if data else ""

    def get_invocation_logs(
        self,
        app_service_id: str,
        job_id: str,
        invocation_id: str,
        task_id: str,
    ) -> AppJobInvocationLogs:
        """Poll an invocation logs fetch task.

        While the agent is still working the response status is non-terminal.
        Once COMPLETED, ``result.lines`` holds the captured log lines.

        Args:
            app_service_id: ID of the app service.
            job_id: ID of the job.
            invocation_id: ID of the invocation.
            task_id: Task ID returned by :meth:`request_invocation_logs`.
        """
        data = self._http.get(
            f"/app-services/{app_service_id}/jobs/{job_id}/invocations/{invocation_id}/logs",
            params={"task_id": task_id},
        )
        return AppJobInvocationLogs.from_dict(data)


class AsyncAppJobsAPI:
    """Manages app jobs for a FoundryDB app service (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Job definitions
    # ------------------------------------------------------------------

    async def create(
        self,
        app_service_id: str,
        *,
        name: str,
        schedule_cron: Optional[str] = None,
        timezone: str = "UTC",
        enabled: Optional[bool] = None,
        image_ref: Optional[str] = None,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        retry_backoff_seconds: Optional[int] = None,
        max_runtime_seconds: Optional[int] = None,
        concurrency_cap: Optional[int] = None,
    ) -> AppJob:
        """Create a job definition on an app service."""
        body: Dict[str, Any] = {"name": name}
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if timezone:
            body["timezone"] = timezone
        if enabled is not None:
            body["enabled"] = enabled
        if image_ref is not None:
            body["image_ref"] = image_ref
        if command is not None:
            body["command"] = command
        if env is not None:
            body["env"] = env
        if max_retries is not None:
            body["max_retries"] = max_retries
        if retry_backoff_seconds is not None:
            body["retry_backoff_seconds"] = retry_backoff_seconds
        if max_runtime_seconds is not None:
            body["max_runtime_seconds"] = max_runtime_seconds
        if concurrency_cap is not None:
            body["concurrency_cap"] = concurrency_cap
        data = await self._http.post(f"/app-services/{app_service_id}/jobs", body)
        return AppJob.from_dict(data)

    async def list(self, app_service_id: str) -> List[AppJob]:
        """Return the job definitions of an app service, oldest first."""
        data = await self._http.get(f"/app-services/{app_service_id}/jobs")
        return [AppJob.from_dict(j) for j in data.get("jobs", [])]

    async def get(self, app_service_id: str, job_id: str) -> Optional[AppJob]:
        """Return one job definition, or ``None`` when not found."""
        try:
            data = await self._http.get(
                f"/app-services/{app_service_id}/jobs/{job_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return AppJob.from_dict(data)

    async def update(
        self,
        app_service_id: str,
        job_id: str,
        *,
        schedule_cron: Optional[str] = None,
        clear_schedule: bool = False,
        timezone: Optional[str] = None,
        enabled: Optional[bool] = None,
        image_ref: Optional[str] = None,
        clear_image_ref: bool = False,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        retry_backoff_seconds: Optional[int] = None,
        max_runtime_seconds: Optional[int] = None,
        concurrency_cap: Optional[int] = None,
    ) -> AppJob:
        """Apply a partial update to a job definition."""
        body: Dict[str, Any] = {}
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if clear_schedule:
            body["clear_schedule"] = True
        if timezone is not None:
            body["timezone"] = timezone
        if enabled is not None:
            body["enabled"] = enabled
        if image_ref is not None:
            body["image_ref"] = image_ref
        if clear_image_ref:
            body["clear_image_ref"] = True
        if command is not None:
            body["command"] = command
        if env is not None:
            body["env"] = env
        if max_retries is not None:
            body["max_retries"] = max_retries
        if retry_backoff_seconds is not None:
            body["retry_backoff_seconds"] = retry_backoff_seconds
        if max_runtime_seconds is not None:
            body["max_runtime_seconds"] = max_runtime_seconds
        if concurrency_cap is not None:
            body["concurrency_cap"] = concurrency_cap
        data = await self._http.patch(
            f"/app-services/{app_service_id}/jobs/{job_id}", body
        )
        return AppJob.from_dict(data)

    async def delete(self, app_service_id: str, job_id: str) -> None:
        """Delete a job definition and its invocation history (idempotent)."""
        try:
            await self._http.delete(
                f"/app-services/{app_service_id}/jobs/{job_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return
            raise

    # ------------------------------------------------------------------
    # Invocations
    # ------------------------------------------------------------------

    async def run(self, app_service_id: str, job_id: str) -> AppJobInvocation:
        """Trigger a manual invocation and return the queued invocation."""
        data = await self._http.post(
            f"/app-services/{app_service_id}/jobs/{job_id}/run"
        )
        return AppJobInvocation.from_dict(data)

    async def list_invocations(
        self,
        app_service_id: str,
        job_id: str,
        *,
        limit: int = 0,
        offset: int = 0,
    ) -> List[AppJobInvocation]:
        """Return the invocation history of a job, newest first."""
        params: Dict[str, Any] = {}
        if limit > 0:
            params["limit"] = limit
        if offset > 0:
            params["offset"] = offset
        data = await self._http.get(
            f"/app-services/{app_service_id}/jobs/{job_id}/invocations",
            params=params or None,
        )
        return [AppJobInvocation.from_dict(i) for i in data.get("invocations", [])]

    async def get_invocation(
        self, app_service_id: str, job_id: str, invocation_id: str
    ) -> Optional[AppJobInvocation]:
        """Return one invocation, or ``None`` when not found."""
        try:
            data = await self._http.get(
                f"/app-services/{app_service_id}/jobs/{job_id}/invocations/{invocation_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return AppJobInvocation.from_dict(data)

    async def request_invocation_logs(
        self,
        app_service_id: str,
        job_id: str,
        invocation_id: str,
        *,
        lines: int = 0,
    ) -> str:
        """Ask the agent to fetch the logs of one invocation.

        Returns the task ID to poll with :meth:`get_invocation_logs`.
        """
        path = f"/app-services/{app_service_id}/jobs/{job_id}/invocations/{invocation_id}/logs"
        params: Dict[str, Any] = {}
        if lines > 0:
            params["lines"] = lines
        data = await self._http.post(path, params or None)
        return data.get("task_id", "") if data else ""

    async def get_invocation_logs(
        self,
        app_service_id: str,
        job_id: str,
        invocation_id: str,
        task_id: str,
    ) -> AppJobInvocationLogs:
        """Poll an invocation logs fetch task."""
        data = await self._http.get(
            f"/app-services/{app_service_id}/jobs/{job_id}/invocations/{invocation_id}/logs",
            params={"task_id": task_id},
        )
        return AppJobInvocationLogs.from_dict(data)
