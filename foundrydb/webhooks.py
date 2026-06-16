"""
FoundryDB SDK - Webhooks and Events API (sync and async).

Webhooks deliver signed event notifications to customer HTTP endpoints.
The event feed is a cursor-paginated log of all events visible to the
authenticated user across their services and organizations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    WebhookEndpoint,
    WebhookDelivery,
    Event,
    EventPage,
)


class WebhooksAPI:
    """Manages webhook endpoints and queries the event feed (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    @staticmethod
    def _base(org_id: str) -> str:
        return f"/organizations/{org_id}/webhooks"

    # ------------------------------------------------------------------
    # Endpoint management
    # ------------------------------------------------------------------

    def create(
        self,
        org_id: str,
        *,
        url: str,
        events: Optional[List[str]] = None,
    ) -> WebhookEndpoint:
        """Register a webhook endpoint for an organization.

        The returned endpoint includes the signing secret exactly once.
        An empty ``events`` list subscribes the endpoint to every event type.

        Args:
            org_id: Organization ID.
            url: The HTTPS URL the platform POSTs events to.
            events: List of event types to subscribe to. Pass an empty list
                or omit to subscribe to all events.
        """
        body: Dict[str, Any] = {"url": url, "events": events or []}
        data = self._http.post(self._base(org_id), body)
        return WebhookEndpoint.from_dict(data)

    def list(self, org_id: str) -> List[WebhookEndpoint]:
        """Return all webhook endpoints of an organization."""
        data = self._http.get(self._base(org_id))
        return [WebhookEndpoint.from_dict(e) for e in data.get("webhooks", [])]

    def get(self, org_id: str, webhook_id: str) -> Optional[WebhookEndpoint]:
        """Return one webhook endpoint, or ``None`` when not found."""
        try:
            data = self._http.get(f"{self._base(org_id)}/{webhook_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return WebhookEndpoint.from_dict(data)

    def delete(self, org_id: str, webhook_id: str) -> None:
        """Remove a webhook endpoint from an organization."""
        self._http.delete(f"{self._base(org_id)}/{webhook_id}")

    def test(self, org_id: str, webhook_id: str) -> None:
        """Enqueue a test event delivery, bypassing the event-type filter."""
        self._http.post(f"{self._base(org_id)}/{webhook_id}/test")

    def enable(self, org_id: str, webhook_id: str) -> None:
        """Re-enable a webhook that was disabled manually or auto-disabled
        after persistent delivery failures, clearing its failure streak."""
        self._http.post(f"{self._base(org_id)}/{webhook_id}/enable")

    def rotate_secret(self, org_id: str, webhook_id: str) -> str:
        """Replace the signing secret of a webhook endpoint.

        The previous secret stops being used immediately. Returns the new
        secret.
        """
        data = self._http.post(f"{self._base(org_id)}/{webhook_id}/rotate-secret")
        return data.get("secret", "") if data else ""

    # ------------------------------------------------------------------
    # Delivery history
    # ------------------------------------------------------------------

    def list_deliveries(
        self, org_id: str, webhook_id: str
    ) -> List[WebhookDelivery]:
        """Return the most recent deliveries for a webhook endpoint."""
        data = self._http.get(f"{self._base(org_id)}/{webhook_id}/deliveries")
        return [WebhookDelivery.from_dict(d) for d in data.get("deliveries", [])]

    def replay_delivery(
        self, org_id: str, webhook_id: str, delivery_id: str
    ) -> WebhookDelivery:
        """Enqueue a fresh delivery re-sending the payload of a prior delivery.

        Returns the new delivery record.
        """
        data = self._http.post(
            f"{self._base(org_id)}/{webhook_id}/deliveries/{delivery_id}/replay"
        )
        return WebhookDelivery.from_dict(data)

    # ------------------------------------------------------------------
    # Event feed
    # ------------------------------------------------------------------

    def list_events(
        self,
        *,
        cursor: int = 0,
        limit: int = 0,
        event_type: str = "",
    ) -> EventPage:
        """Return one page of the cursor-paginated event feed.

        Args:
            cursor: ``next_cursor`` value from a previous page. 0 starts at
                the newest event.
            limit: Page size cap (server default 50, maximum 200).
            event_type: Filter to a single event type when non-empty.
        """
        params: Dict[str, Any] = {}
        if cursor > 0:
            params["cursor"] = cursor
        if limit > 0:
            params["limit"] = limit
        if event_type:
            params["event_type"] = event_type
        data = self._http.get("/events", params=params or None)
        return EventPage.from_dict(data)


class AsyncWebhooksAPI:
    """Manages webhook endpoints and queries the event feed (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    @staticmethod
    def _base(org_id: str) -> str:
        return f"/organizations/{org_id}/webhooks"

    async def create(
        self,
        org_id: str,
        *,
        url: str,
        events: Optional[List[str]] = None,
    ) -> WebhookEndpoint:
        """Register a webhook endpoint for an organization."""
        body: Dict[str, Any] = {"url": url, "events": events or []}
        data = await self._http.post(self._base(org_id), body)
        return WebhookEndpoint.from_dict(data)

    async def list(self, org_id: str) -> List[WebhookEndpoint]:
        """Return all webhook endpoints of an organization."""
        data = await self._http.get(self._base(org_id))
        return [WebhookEndpoint.from_dict(e) for e in data.get("webhooks", [])]

    async def get(self, org_id: str, webhook_id: str) -> Optional[WebhookEndpoint]:
        """Return one webhook endpoint, or ``None`` when not found."""
        try:
            data = await self._http.get(f"{self._base(org_id)}/{webhook_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return WebhookEndpoint.from_dict(data)

    async def delete(self, org_id: str, webhook_id: str) -> None:
        """Remove a webhook endpoint from an organization."""
        await self._http.delete(f"{self._base(org_id)}/{webhook_id}")

    async def test(self, org_id: str, webhook_id: str) -> None:
        """Enqueue a test event delivery."""
        await self._http.post(f"{self._base(org_id)}/{webhook_id}/test")

    async def enable(self, org_id: str, webhook_id: str) -> None:
        """Re-enable a disabled webhook endpoint."""
        await self._http.post(f"{self._base(org_id)}/{webhook_id}/enable")

    async def rotate_secret(self, org_id: str, webhook_id: str) -> str:
        """Replace the signing secret. Returns the new secret."""
        data = await self._http.post(
            f"{self._base(org_id)}/{webhook_id}/rotate-secret"
        )
        return data.get("secret", "") if data else ""

    async def list_deliveries(
        self, org_id: str, webhook_id: str
    ) -> List[WebhookDelivery]:
        """Return the most recent deliveries for a webhook endpoint."""
        data = await self._http.get(
            f"{self._base(org_id)}/{webhook_id}/deliveries"
        )
        return [WebhookDelivery.from_dict(d) for d in data.get("deliveries", [])]

    async def replay_delivery(
        self, org_id: str, webhook_id: str, delivery_id: str
    ) -> WebhookDelivery:
        """Enqueue a fresh delivery re-sending the payload of a prior delivery."""
        data = await self._http.post(
            f"{self._base(org_id)}/{webhook_id}/deliveries/{delivery_id}/replay"
        )
        return WebhookDelivery.from_dict(data)

    async def list_events(
        self,
        *,
        cursor: int = 0,
        limit: int = 0,
        event_type: str = "",
    ) -> EventPage:
        """Return one page of the cursor-paginated event feed."""
        params: Dict[str, Any] = {}
        if cursor > 0:
            params["cursor"] = cursor
        if limit > 0:
            params["limit"] = limit
        if event_type:
            params["event_type"] = event_type
        data = await self._http.get("/events", params=params or None)
        return EventPage.from_dict(data)
