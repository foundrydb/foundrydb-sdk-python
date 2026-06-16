"""
FoundryDB SDK - Organizations API (sync and async).
"""
from __future__ import annotations

from typing import List, Optional

from .client import AsyncHTTPClient, HTTPClient
from .types import Organization


class OrganizationsAPI:
    """Access and list FoundryDB organizations (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self) -> List[Organization]:
        """List all organizations the authenticated user belongs to.

        Returns a list of :class:`~foundrydb.types.Organization` objects,
        including both personal and team organizations.
        """
        data = self._http.get("/organizations/")
        organizations = data.get("organizations") if isinstance(data, dict) else data
        return [Organization.from_dict(o) for o in (organizations or [])]

    def get(self, org_id: str) -> Optional[Organization]:
        """Return one organization by ID.

        Returns ``None`` when the organization does not exist (404) or the
        authenticated user does not belong to it.

        Args:
            org_id: UUID of the organization.
        """
        try:
            data = self._http.get(f"/organizations/{org_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return Organization.from_dict(data)


class AsyncOrganizationsAPI:
    """Access and list FoundryDB organizations (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(self) -> List[Organization]:
        """List all organizations the authenticated user belongs to.

        Returns a list of :class:`~foundrydb.types.Organization` objects,
        including both personal and team organizations.
        """
        data = await self._http.get("/organizations/")
        organizations = data.get("organizations") if isinstance(data, dict) else data
        return [Organization.from_dict(o) for o in (organizations or [])]

    async def get(self, org_id: str) -> Optional[Organization]:
        """Return one organization by ID, or ``None`` when not found.

        Args:
            org_id: UUID of the organization.
        """
        try:
            data = await self._http.get(f"/organizations/{org_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return Organization.from_dict(data)
