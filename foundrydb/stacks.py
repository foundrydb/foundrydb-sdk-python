"""
FoundryDB SDK - Stacks API (sync and async).

Stacks are pre-wired vertical starter environments that compose platform
primitives (databases, file services, inference keys, app services) into a
running application with a single launch call. Provisioning is asynchronous:
a new stack starts in Pending and reaches Running once all constituent
resources are ready.

Phase 2 extends the surface with a customer-authored template marketplace:
organizations can create, publish, and consume custom stack templates.
Running stacks can be upgraded to a newer template version via a two-step
preview-then-apply flow.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    CustomStackTemplate,
    CustomTemplateRequest,
    Stack,
    StackCostPreview,
    StackMigration,
    StackTemplate,
    StackUpgradePlan,
)


class StacksAPI:
    """Manages FoundryDB vertical-starter stacks (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # First-party template catalog
    # ------------------------------------------------------------------

    def list_stack_templates(self) -> List[StackTemplate]:
        """Return the catalog of available first-party stack templates."""
        data = self._http.get("/stacks/templates")
        return [StackTemplate.from_dict(t) for t in data.get("templates", [])]

    def preview_stack(
        self,
        *,
        template_name: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> StackCostPreview:
        """Return a cost breakdown for launching a stack template.

        Call this before ``launch_stack`` to show the user a binding monthly
        cost estimate. The preview is required because ``launch_stack`` demands
        ``accepted_monthly_cost``. Provide exactly one of ``template_name``
        (first-party catalog) or ``template_id`` (custom marketplace template).

        Args:
            template_name: Identifier of a first-party template (e.g. ``"rag-chatbot"``).
            template_id: ID of a custom stack template from the marketplace.
        """
        body: Dict[str, Any] = {}
        if template_name is not None:
            body["template_name"] = template_name
        if template_id is not None:
            body["template_id"] = template_id
        data = self._http.post("/stacks/preview", body)
        return StackCostPreview.from_dict(data)

    # ------------------------------------------------------------------
    # Stack lifecycle
    # ------------------------------------------------------------------

    def launch_stack(
        self,
        *,
        name: str,
        template_name: Optional[str] = None,
        template_id: Optional[str] = None,
        accepted_monthly_cost: float,
        organization_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "Stack":
        """Launch a new stack from a template.

        Returns a ``Stack`` in Pending status. The platform provisions each
        constituent resource in dependency order; poll ``get_stack`` or call
        ``wait_for_stack_running`` until ``status`` is ``"Running"``.

        Provide exactly one of ``template_name`` (first-party catalog) or
        ``template_id`` (custom marketplace template).

        Args:
            name: Display name for the stack.
            template_name: Identifier of a first-party template to use.
            template_id: ID of a custom stack template from the marketplace.
            accepted_monthly_cost: The monthly cost shown by ``preview_stack``
                that the caller explicitly accepts. Must match the preview or
                the request is rejected.
            organization_id: Assign the stack to an organization.
            overrides: Optional template parameter overrides (e.g. plan,
                zone, storage size).
        """
        body: Dict[str, Any] = {
            "name": name,
            "accepted_monthly_cost": accepted_monthly_cost,
        }
        if template_name is not None:
            body["template_name"] = template_name
        if template_id is not None:
            body["template_id"] = template_id
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
    # Custom template marketplace (Phase 2)
    # ------------------------------------------------------------------

    def create_stack_template(self, request: CustomTemplateRequest) -> CustomStackTemplate:
        """Create a new custom stack template owned by the caller's organization.

        The template starts in ``draft`` / ``private`` publication status.
        Use ``publish_stack_template`` to submit it for marketplace listing.

        Args:
            request: Template definition including display name, version,
                description, and resource descriptors.
        """
        data = self._http.post("/stacks/templates", request.to_dict())
        return CustomStackTemplate.from_dict(data)

    def list_my_stack_templates(self) -> List[CustomStackTemplate]:
        """Return all custom stack templates owned by the authenticated organization."""
        data = self._http.get("/stacks/templates/mine")
        return [CustomStackTemplate.from_dict(t) for t in data.get("templates", [])]

    def list_marketplace_stack_templates(self) -> List[CustomStackTemplate]:
        """Return all published custom stack templates available in the marketplace."""
        data = self._http.get("/stacks/templates/marketplace")
        return [CustomStackTemplate.from_dict(t) for t in data.get("templates", [])]

    def get_stack_template(self, template_id: str) -> CustomStackTemplate:
        """Return a custom stack template by ID.

        Args:
            template_id: ID of the custom stack template to retrieve.
        """
        data = self._http.get(f"/stacks/templates/{template_id}")
        return CustomStackTemplate.from_dict(data)

    def update_stack_template(
        self,
        template_id: str,
        request: CustomTemplateRequest,
    ) -> CustomStackTemplate:
        """Update an existing custom stack template.

        Only the owning organization may update a template. Updates are
        accepted regardless of the current publication status; re-publishing
        after an update re-triggers the review flow.

        Args:
            template_id: ID of the custom stack template to update.
            request: Updated template definition.
        """
        data = self._http.patch(f"/stacks/templates/{template_id}", request.to_dict())
        return CustomStackTemplate.from_dict(data)

    def delete_stack_template(self, template_id: str) -> None:
        """Delete a custom stack template.

        Only draft or unpublished templates may be deleted. Published templates
        must be unpublished first.

        Args:
            template_id: ID of the custom stack template to delete.
        """
        self._http.delete(f"/stacks/templates/{template_id}")

    def publish_stack_template(self, template_id: str) -> CustomStackTemplate:
        """Submit a custom stack template for marketplace publication.

        Transitions the template to ``pending_review``. The platform
        reviews the template and, if approved, sets it to ``published``.

        Args:
            template_id: ID of the custom stack template to publish.
        """
        data = self._http.post(f"/stacks/templates/{template_id}/publish")
        return CustomStackTemplate.from_dict(data)

    def unpublish_stack_template(self, template_id: str) -> CustomStackTemplate:
        """Remove a custom stack template from the marketplace.

        Transitions the template from ``published`` back to ``unpublished``.
        Existing stacks launched from this template continue running; new
        launches are blocked.

        Args:
            template_id: ID of the custom stack template to unpublish.
        """
        data = self._http.post(f"/stacks/templates/{template_id}/unpublish")
        return CustomStackTemplate.from_dict(data)

    # ------------------------------------------------------------------
    # Stack upgrade (Phase 2)
    # ------------------------------------------------------------------

    def preview_stack_upgrade(
        self,
        stack_id: str,
        *,
        target_template_id: Optional[str] = None,
        target_version: Optional[str] = None,
    ) -> StackUpgradePlan:
        """Preview the resource changes that applying a stack upgrade would make.

        Returns a ``StackUpgradePlan`` describing which resources will be added,
        updated, or removed. Pass the plan's ``to_version`` to ``apply_stack_upgrade``
        once the user confirms.

        Provide either ``target_template_id`` (to upgrade to a specific custom
        template revision) or ``target_version`` (to upgrade to a newer semver
        of the same template).

        Args:
            stack_id: ID of the stack to preview the upgrade for.
            target_template_id: ID of a custom stack template revision to
                upgrade to.
            target_version: Semver version of the current template to upgrade to.
        """
        body: Dict[str, Any] = {}
        if target_template_id is not None:
            body["target_template_id"] = target_template_id
        if target_version is not None:
            body["target_version"] = target_version
        data = self._http.post(f"/stacks/{stack_id}/upgrade/preview", body)
        return StackUpgradePlan.from_dict(data)

    def apply_stack_upgrade(
        self,
        stack_id: str,
        *,
        target_template_id: Optional[str] = None,
        target_version: Optional[str] = None,
        accepted_monthly_cost: Optional[float] = None,
    ) -> StackMigration:
        """Apply a stack upgrade, transitioning the stack to the target template version.

        This is asynchronous: the returned ``StackMigration`` starts in
        ``in_progress`` and reaches ``completed`` or ``failed``. Poll
        ``get_stack`` to observe the stack's overall status during the upgrade.

        Args:
            stack_id: ID of the stack to upgrade.
            target_template_id: ID of a custom stack template revision to
                upgrade to.
            target_version: Semver version of the current template to upgrade to.
            accepted_monthly_cost: The projected cost shown by
                ``preview_stack_upgrade`` that the caller explicitly accepts.
        """
        body: Dict[str, Any] = {}
        if target_template_id is not None:
            body["target_template_id"] = target_template_id
        if target_version is not None:
            body["target_version"] = target_version
        if accepted_monthly_cost is not None:
            body["accepted_monthly_cost"] = accepted_monthly_cost
        data = self._http.post(f"/stacks/{stack_id}/upgrade", body)
        return StackMigration.from_dict(data)

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
    # First-party template catalog
    # ------------------------------------------------------------------

    async def list_stack_templates(self) -> List[StackTemplate]:
        """Return the catalog of available first-party stack templates."""
        data = await self._http.get("/stacks/templates")
        return [StackTemplate.from_dict(t) for t in data.get("templates", [])]

    async def preview_stack(
        self,
        *,
        template_name: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> StackCostPreview:
        """Return a cost breakdown for launching a stack template.

        Provide exactly one of ``template_name`` (first-party catalog) or
        ``template_id`` (custom marketplace template).

        Args:
            template_name: Identifier of a first-party template (e.g. ``"rag-chatbot"``).
            template_id: ID of a custom stack template from the marketplace.
        """
        body: Dict[str, Any] = {}
        if template_name is not None:
            body["template_name"] = template_name
        if template_id is not None:
            body["template_id"] = template_id
        data = await self._http.post("/stacks/preview", body)
        return StackCostPreview.from_dict(data)

    # ------------------------------------------------------------------
    # Stack lifecycle
    # ------------------------------------------------------------------

    async def launch_stack(
        self,
        *,
        name: str,
        template_name: Optional[str] = None,
        template_id: Optional[str] = None,
        accepted_monthly_cost: float,
        organization_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "Stack":
        """Launch a new stack from a template.

        Returns a ``Stack`` in Pending status. Poll ``get_stack`` or call
        ``wait_for_stack_running`` until ``status`` is ``"Running"``.

        Provide exactly one of ``template_name`` (first-party catalog) or
        ``template_id`` (custom marketplace template).

        Args:
            name: Display name for the stack.
            template_name: Identifier of a first-party template to use.
            template_id: ID of a custom stack template from the marketplace.
            accepted_monthly_cost: The monthly cost shown by ``preview_stack``
                that the caller explicitly accepts.
            organization_id: Assign the stack to an organization.
            overrides: Optional template parameter overrides.
        """
        body: Dict[str, Any] = {
            "name": name,
            "accepted_monthly_cost": accepted_monthly_cost,
        }
        if template_name is not None:
            body["template_name"] = template_name
        if template_id is not None:
            body["template_id"] = template_id
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
    # Custom template marketplace (Phase 2)
    # ------------------------------------------------------------------

    async def create_stack_template(
        self, request: CustomTemplateRequest
    ) -> CustomStackTemplate:
        """Create a new custom stack template owned by the caller's organization.

        The template starts in ``draft`` / ``private`` publication status.
        Use ``publish_stack_template`` to submit it for marketplace listing.

        Args:
            request: Template definition including display name, version,
                description, and resource descriptors.
        """
        data = await self._http.post("/stacks/templates", request.to_dict())
        return CustomStackTemplate.from_dict(data)

    async def list_my_stack_templates(self) -> List[CustomStackTemplate]:
        """Return all custom stack templates owned by the authenticated organization."""
        data = await self._http.get("/stacks/templates/mine")
        return [CustomStackTemplate.from_dict(t) for t in data.get("templates", [])]

    async def list_marketplace_stack_templates(self) -> List[CustomStackTemplate]:
        """Return all published custom stack templates available in the marketplace."""
        data = await self._http.get("/stacks/templates/marketplace")
        return [CustomStackTemplate.from_dict(t) for t in data.get("templates", [])]

    async def get_stack_template(self, template_id: str) -> CustomStackTemplate:
        """Return a custom stack template by ID.

        Args:
            template_id: ID of the custom stack template to retrieve.
        """
        data = await self._http.get(f"/stacks/templates/{template_id}")
        return CustomStackTemplate.from_dict(data)

    async def update_stack_template(
        self,
        template_id: str,
        request: CustomTemplateRequest,
    ) -> CustomStackTemplate:
        """Update an existing custom stack template.

        Only the owning organization may update a template. Updates are
        accepted regardless of the current publication status; re-publishing
        after an update re-triggers the review flow.

        Args:
            template_id: ID of the custom stack template to update.
            request: Updated template definition.
        """
        data = await self._http.patch(f"/stacks/templates/{template_id}", request.to_dict())
        return CustomStackTemplate.from_dict(data)

    async def delete_stack_template(self, template_id: str) -> None:
        """Delete a custom stack template.

        Only draft or unpublished templates may be deleted. Published templates
        must be unpublished first.

        Args:
            template_id: ID of the custom stack template to delete.
        """
        await self._http.delete(f"/stacks/templates/{template_id}")

    async def publish_stack_template(self, template_id: str) -> CustomStackTemplate:
        """Submit a custom stack template for marketplace publication.

        Transitions the template to ``pending_review``. The platform
        reviews the template and, if approved, sets it to ``published``.

        Args:
            template_id: ID of the custom stack template to publish.
        """
        data = await self._http.post(f"/stacks/templates/{template_id}/publish")
        return CustomStackTemplate.from_dict(data)

    async def unpublish_stack_template(self, template_id: str) -> CustomStackTemplate:
        """Remove a custom stack template from the marketplace.

        Transitions the template from ``published`` back to ``unpublished``.
        Existing stacks launched from this template continue running; new
        launches are blocked.

        Args:
            template_id: ID of the custom stack template to unpublish.
        """
        data = await self._http.post(f"/stacks/templates/{template_id}/unpublish")
        return CustomStackTemplate.from_dict(data)

    # ------------------------------------------------------------------
    # Stack upgrade (Phase 2)
    # ------------------------------------------------------------------

    async def preview_stack_upgrade(
        self,
        stack_id: str,
        *,
        target_template_id: Optional[str] = None,
        target_version: Optional[str] = None,
    ) -> StackUpgradePlan:
        """Preview the resource changes that applying a stack upgrade would make.

        Returns a ``StackUpgradePlan`` describing which resources will be added,
        updated, or removed. Pass the plan's ``to_version`` to
        ``apply_stack_upgrade`` once the user confirms.

        Provide either ``target_template_id`` or ``target_version``.

        Args:
            stack_id: ID of the stack to preview the upgrade for.
            target_template_id: ID of a custom stack template revision to
                upgrade to.
            target_version: Semver version of the current template to upgrade to.
        """
        body: Dict[str, Any] = {}
        if target_template_id is not None:
            body["target_template_id"] = target_template_id
        if target_version is not None:
            body["target_version"] = target_version
        data = await self._http.post(f"/stacks/{stack_id}/upgrade/preview", body)
        return StackUpgradePlan.from_dict(data)

    async def apply_stack_upgrade(
        self,
        stack_id: str,
        *,
        target_template_id: Optional[str] = None,
        target_version: Optional[str] = None,
        accepted_monthly_cost: Optional[float] = None,
    ) -> StackMigration:
        """Apply a stack upgrade, transitioning the stack to the target template version.

        This is asynchronous: the returned ``StackMigration`` starts in
        ``in_progress`` and reaches ``completed`` or ``failed``. Poll
        ``get_stack`` to observe the stack's overall status during the upgrade.

        Args:
            stack_id: ID of the stack to upgrade.
            target_template_id: ID of a custom stack template revision to
                upgrade to.
            target_version: Semver version of the current template to upgrade to.
            accepted_monthly_cost: The projected cost shown by
                ``preview_stack_upgrade`` that the caller explicitly accepts.
        """
        body: Dict[str, Any] = {}
        if target_template_id is not None:
            body["target_template_id"] = target_template_id
        if target_version is not None:
            body["target_version"] = target_version
        if accepted_monthly_cost is not None:
            body["accepted_monthly_cost"] = accepted_monthly_cost
        data = await self._http.post(f"/stacks/{stack_id}/upgrade", body)
        return StackMigration.from_dict(data)

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
