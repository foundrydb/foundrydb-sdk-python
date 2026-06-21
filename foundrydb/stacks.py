"""
FoundryDB SDK - Stacks API (sync and async).

Stacks are pre-wired vertical starter environments that compose platform
primitives (databases, file services, inference keys, app services) into a
running application with a single launch call. Provisioning is asynchronous:
a new stack starts in Pending and reaches Running once all constituent
resources are ready.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    Stack,
    StackCostPreview,
    StackTemplate,
)


class StacksAPI:
    """Manages FoundryDB vertical-starter stacks (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def list_stack_templates(self) -> List[StackTemplate]:
        """Return the catalog of available stack templates."""
        data = self._http.get("/stacks/templates")
        return [StackTemplate.from_dict(t) for t in data.get("templates", [])]

    def preview_stack(self, *, template_name: str) -> StackCostPreview:
        """Return a cost breakdown for launching a stack template.

        Call this before ``launch_stack`` to show the user a binding monthly
        cost estimate. The preview is required because ``launch_stack`` demands
        ``accepted_monthly_cost``.

        Args:
            template_name: Identifier of the stack template (e.g. ``"rag-chatbot"``).
        """
        body: Dict[str, Any] = {"template_name": template_name}
        data = self._http.post("/stacks/preview", body)
        return StackCostPreview.from_dict(data)

    # ------------------------------------------------------------------
    # Stack lifecycle
    # ------------------------------------------------------------------

    def launch_stack(
        self,
        *,
        name: str,
        template_name: str,
        accepted_monthly_cost: float,
        organization_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "Stack":
        """Launch a new stack from a template.

        Returns a ``Stack`` in Pending status. The platform provisions each
        constituent resource in dependency order; poll ``get_stack`` or call
        ``wait_for_stack_running`` until ``status`` is ``"Running"``.

        Args:
            name: Display name for the stack.
            template_name: Identifier of the stack template to use.
            accepted_monthly_cost: The monthly cost shown by ``preview_stack``
                that the caller explicitly accepts. Must match the preview or
                the request is rejected.
            organization_id: Assign the stack to an organization.
            overrides: Optional template parameter overrides (e.g. plan,
                zone, storage size).
        """
        body: Dict[str, Any] = {
            "name": name,
            "template_name": template_name,
            "accepted_monthly_cost": accepted_monthly_cost,
        }
        if organization_id is not None:
            body["organization_id"] = organization_id
        if overrides is not None:
            body["overrides"] = overrides
        data = self._http.post("/stacks", body)
        return Stack.from_dict(data)

    def list_stacks(self) -> List["Stack"]:
        """Return all stacks visible to the authenticated user."""
        data = self._http.get("/stacks")
        return [Stack.from_dict(s) for s in data.get("stacks", [])]

    def get_stack(self, stack_id: str) -> "Stack":
        """Return a stack by ID.

        Args:
            stack_id: ID of the stack to retrieve.
        """
        data = self._http.get(f"/stacks/{stack_id}")
        return Stack.from_dict(data)

    def delete_stack(self, stack_id: str) -> str:
        """Delete a stack and all its constituent resources.

        Returns the ``status`` string from the API response (typically
        ``"Deleting"``). Deletion is asynchronous; poll ``get_stack`` until
        ``status`` is ``"Deleted"``.

        Args:
            stack_id: ID of the stack to delete.
        """
        data = self._http.delete(f"/stacks/{stack_id}")
        return data.get("status", "Deleting") if data else "Deleting"

    def retry_stack(self, stack_id: str) -> str:
        """Retry a stack that is in Failed status.

        Returns the ``status`` string from the API response. The platform
        resumes provisioning from the first failed resource.

        Args:
            stack_id: ID of the stack to retry.
        """
        data = self._http.post(f"/stacks/{stack_id}/retry")
        return data.get("status", "Provisioning") if data else "Provisioning"

    # ------------------------------------------------------------------
    # Polling helper
    # ------------------------------------------------------------------

    def wait_for_stack_running(
        self,
        stack_id: str,
        *,
        timeout_seconds: float = 900.0,
        poll_interval_seconds: float = 10.0,
    ) -> "Stack":
        """Block until a stack reaches ``Running`` status, then return it.

        Raises ``TimeoutError`` when ``timeout_seconds`` elapses without the
        stack reaching a terminal state, and ``RuntimeError`` when the stack
        reaches ``Failed``.

        Args:
            stack_id: ID of the stack to wait for.
            timeout_seconds: Maximum time to wait before raising
                ``TimeoutError`` (default 900 s / 15 min).
            poll_interval_seconds: Seconds to sleep between status checks
                (default 10 s).
        """
        deadline = time.monotonic() + timeout_seconds
        terminal_ok = {"Running"}
        terminal_fail = {"Failed"}
        while True:
            stack = self.get_stack(stack_id)
            if stack.status in terminal_ok:
                return stack
            if stack.status in terminal_fail:
                detail = stack.status_detail or ""
                raise RuntimeError(
                    f"Stack {stack_id} reached Failed status: {detail}"
                )
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Stack {stack_id} did not reach Running within"
                    f" {timeout_seconds}s (current status: {stack.status})"
                )
            time.sleep(poll_interval_seconds)


class AsyncStacksAPI:
    """Manages FoundryDB vertical-starter stacks (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    async def list_stack_templates(self) -> List[StackTemplate]:
        """Return the catalog of available stack templates."""
        data = await self._http.get("/stacks/templates")
        return [StackTemplate.from_dict(t) for t in data.get("templates", [])]

    async def preview_stack(self, *, template_name: str) -> StackCostPreview:
        """Return a cost breakdown for launching a stack template.

        Args:
            template_name: Identifier of the stack template (e.g. ``"rag-chatbot"``).
        """
        body: Dict[str, Any] = {"template_name": template_name}
        data = await self._http.post("/stacks/preview", body)
        return StackCostPreview.from_dict(data)

    # ------------------------------------------------------------------
    # Stack lifecycle
    # ------------------------------------------------------------------

    async def launch_stack(
        self,
        *,
        name: str,
        template_name: str,
        accepted_monthly_cost: float,
        organization_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "Stack":
        """Launch a new stack from a template.

        Returns a ``Stack`` in Pending status. Poll ``get_stack`` or call
        ``wait_for_stack_running`` until ``status`` is ``"Running"``.

        Args:
            name: Display name for the stack.
            template_name: Identifier of the stack template to use.
            accepted_monthly_cost: The monthly cost shown by ``preview_stack``
                that the caller explicitly accepts.
            organization_id: Assign the stack to an organization.
            overrides: Optional template parameter overrides.
        """
        body: Dict[str, Any] = {
            "name": name,
            "template_name": template_name,
            "accepted_monthly_cost": accepted_monthly_cost,
        }
        if organization_id is not None:
            body["organization_id"] = organization_id
        if overrides is not None:
            body["overrides"] = overrides
        data = await self._http.post("/stacks", body)
        return Stack.from_dict(data)

    async def list_stacks(self) -> List["Stack"]:
        """Return all stacks visible to the authenticated user."""
        data = await self._http.get("/stacks")
        return [Stack.from_dict(s) for s in data.get("stacks", [])]

    async def get_stack(self, stack_id: str) -> "Stack":
        """Return a stack by ID.

        Args:
            stack_id: ID of the stack to retrieve.
        """
        data = await self._http.get(f"/stacks/{stack_id}")
        return Stack.from_dict(data)

    async def delete_stack(self, stack_id: str) -> str:
        """Delete a stack and all its constituent resources.

        Returns the ``status`` string from the API response (typically
        ``"Deleting"``). Deletion is asynchronous; poll ``get_stack`` until
        ``status`` is ``"Deleted"``.

        Args:
            stack_id: ID of the stack to delete.
        """
        data = await self._http.delete(f"/stacks/{stack_id}")
        return data.get("status", "Deleting") if data else "Deleting"

    async def retry_stack(self, stack_id: str) -> str:
        """Retry a stack that is in Failed status.

        Returns the ``status`` string from the API response. The platform
        resumes provisioning from the first failed resource.

        Args:
            stack_id: ID of the stack to retry.
        """
        data = await self._http.post(f"/stacks/{stack_id}/retry")
        return data.get("status", "Provisioning") if data else "Provisioning"

    # ------------------------------------------------------------------
    # Polling helper
    # ------------------------------------------------------------------

    async def wait_for_stack_running(
        self,
        stack_id: str,
        *,
        timeout_seconds: float = 900.0,
        poll_interval_seconds: float = 10.0,
    ) -> "Stack":
        """Await until a stack reaches ``Running`` status, then return it.

        Raises ``TimeoutError`` when ``timeout_seconds`` elapses without the
        stack reaching a terminal state, and ``RuntimeError`` when the stack
        reaches ``Failed``.

        Args:
            stack_id: ID of the stack to wait for.
            timeout_seconds: Maximum time to wait before raising
                ``TimeoutError`` (default 900 s / 15 min).
            poll_interval_seconds: Seconds to sleep between status checks
                (default 10 s).
        """
        import asyncio

        deadline = time.monotonic() + timeout_seconds
        terminal_ok = {"Running"}
        terminal_fail = {"Failed"}
        while True:
            stack = await self.get_stack(stack_id)
            if stack.status in terminal_ok:
                return stack
            if stack.status in terminal_fail:
                detail = stack.status_detail or ""
                raise RuntimeError(
                    f"Stack {stack_id} reached Failed status: {detail}"
                )
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Stack {stack_id} did not reach Running within"
                    f" {timeout_seconds}s (current status: {stack.status})"
                )
            await asyncio.sleep(poll_interval_seconds)
