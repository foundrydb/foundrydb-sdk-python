"""
FoundryDB SDK - AI Actions API (sync and async).

Three surfaces:
  1. Feed - a prioritized list of platform-generated recommendations across the
     caller's services (index suggestions, advisories).
  2. Copilot - turns a natural-language intent into a previewable plan without
     executing anything.
  3. Executor - executes one confirm-tier action by delegating to the existing
     brokered, audited handler. Destructive (typed_confirm) actions are
     intentionally excluded and must be executed through the service's native
     API.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    AIActionsResponse,
    CopilotPlan,
    ExecuteAIActionResult,
    AIActionExecutionListResponse,
    AIActionRollbackResult,
)


class AIActionsAPI:
    """AI Actions feed, copilot, and execution surfaces (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
        *,
        service_id: str = "",
        kind: str = "",
        severity: str = "",
        limit: int = 0,
    ) -> AIActionsResponse:
        """Return the prioritized AI actions feed across the caller's services.

        Args:
            service_id: Filter to one service. Must be visible to the caller.
            kind: ``"index"`` or ``"advisory"``.
            severity: Minimum severity: ``"info"``, ``"warning"``, or
                ``"critical"``.
            limit: Max items to return (server default 50, max 200).
        """
        params: Dict[str, Any] = {}
        if service_id:
            params["service_id"] = service_id
        if kind:
            params["kind"] = kind
        if severity:
            params["severity"] = severity
        if limit > 0:
            params["limit"] = limit
        data = self._http.get("/ai/actions", params=params or None)
        return AIActionsResponse.from_dict(data)

    def copilot_plan(
        self,
        *,
        intent: str,
        service_id: str = "",
    ) -> CopilotPlan:
        """Turn a natural-language intent into a previewable plan.

        The plan executes nothing. The server returns 501 when no model
        provider is configured for the organization.

        Args:
            intent: The natural-language intent to plan for.
            service_id: Optional context service. Must be visible to the
                caller.
        """
        body: Dict[str, Any] = {"intent": intent}
        if service_id:
            body["service_id"] = service_id
        data = self._http.post("/ai/copilot/plan", body)
        return CopilotPlan.from_dict(data)

    def execute(
        self,
        *,
        action_type: str,
        service_id: str,
        args: Optional[Dict[str, Any]] = None,
        confirm: bool = True,
    ) -> ExecuteAIActionResult:
        """Execute one confirm-tier action by delegating to its brokered handler.

        ``confirm`` must be ``True``; unknown or destructive (typed_confirm)
        action types are rejected by the server. When the gate accepts and
        delegates, inspect ``status`` and ``http_status`` on the result for
        the inner handler's real outcome.

        Supported confirm-tier action types in v1:
          - ``apply_index_recommendation``: args ``recommendation_id``
          - ``dismiss_advisory``: args ``advisory_match_id``, ``reason``
          - ``scale_service``: args ``target_plan_name`` or ``cpu_cores`` +
            ``memory_mb``; optional ``storage_mb``
          - ``add_replica``: args ``node_name``, ``zone``; optional
            ``cpu_cores``, ``memory_mb``, ``storage_mb``

        Args:
            action_type: The confirm-tier action type to execute.
            service_id: ID of the service the action targets.
            args: Action-specific arguments.
            confirm: Must be ``True`` for confirm-tier actions.
        """
        body: Dict[str, Any] = {
            "action_type": action_type,
            "service_id": service_id,
            "confirm": confirm,
        }
        if args is not None:
            body["args"] = args
        data = self._http.post("/ai/actions/execute", body)
        return ExecuteAIActionResult.from_dict(data)

    def list_executions(
        self,
        *,
        service_id: str = "",
        limit: int = 0,
    ) -> AIActionExecutionListResponse:
        """Return the outcome-loop execution history, newest first.

        Args:
            service_id: Filter to one service. Must be visible to the caller.
            limit: Max records (server default 50, max 200).
        """
        params: Dict[str, Any] = {}
        if service_id:
            params["service_id"] = service_id
        if limit > 0:
            params["limit"] = limit
        data = self._http.get("/ai/actions/executions", params=params or None)
        return AIActionExecutionListResponse.from_dict(data)

    def rollback_execution(self, execution_id: str) -> AIActionRollbackResult:
        """Reverse a reversible execution.

        Reversibility is decided by the recorded action type:
          - ``apply_index_recommendation``: drops the created index (async,
            ``revert_status`` is ``"requested"``).
          - ``dismiss_advisory``: reactivates the advisory (sync, ``"done"``).
          - ``scale_service`` and ``add_replica``: not reversible (422).

        The server returns 404 when the execution is not found or its service
        is not visible to the caller.

        Args:
            execution_id: ID of the execution to roll back.
        """
        data = self._http.post(f"/ai/actions/executions/{execution_id}/rollback")
        return AIActionRollbackResult.from_dict(data)


class AsyncAIActionsAPI:
    """AI Actions feed, copilot, and execution surfaces (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        service_id: str = "",
        kind: str = "",
        severity: str = "",
        limit: int = 0,
    ) -> AIActionsResponse:
        """Return the prioritized AI actions feed across the caller's services."""
        params: Dict[str, Any] = {}
        if service_id:
            params["service_id"] = service_id
        if kind:
            params["kind"] = kind
        if severity:
            params["severity"] = severity
        if limit > 0:
            params["limit"] = limit
        data = await self._http.get("/ai/actions", params=params or None)
        return AIActionsResponse.from_dict(data)

    async def copilot_plan(
        self,
        *,
        intent: str,
        service_id: str = "",
    ) -> CopilotPlan:
        """Turn a natural-language intent into a previewable plan."""
        body: Dict[str, Any] = {"intent": intent}
        if service_id:
            body["service_id"] = service_id
        data = await self._http.post("/ai/copilot/plan", body)
        return CopilotPlan.from_dict(data)

    async def execute(
        self,
        *,
        action_type: str,
        service_id: str,
        args: Optional[Dict[str, Any]] = None,
        confirm: bool = True,
    ) -> ExecuteAIActionResult:
        """Execute one confirm-tier action."""
        body: Dict[str, Any] = {
            "action_type": action_type,
            "service_id": service_id,
            "confirm": confirm,
        }
        if args is not None:
            body["args"] = args
        data = await self._http.post("/ai/actions/execute", body)
        return ExecuteAIActionResult.from_dict(data)

    async def list_executions(
        self,
        *,
        service_id: str = "",
        limit: int = 0,
    ) -> AIActionExecutionListResponse:
        """Return the outcome-loop execution history, newest first."""
        params: Dict[str, Any] = {}
        if service_id:
            params["service_id"] = service_id
        if limit > 0:
            params["limit"] = limit
        data = await self._http.get("/ai/actions/executions", params=params or None)
        return AIActionExecutionListResponse.from_dict(data)

    async def rollback_execution(self, execution_id: str) -> AIActionRollbackResult:
        """Reverse a reversible execution."""
        data = await self._http.post(
            f"/ai/actions/executions/{execution_id}/rollback"
        )
        return AIActionRollbackResult.from_dict(data)
