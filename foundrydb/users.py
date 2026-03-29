"""
FoundryDB SDK - Users API (sync and async).
"""
from __future__ import annotations

from typing import List

from .client import HTTPClient, AsyncHTTPClient
from .types import DatabaseUser, RevealPasswordResponse


class UsersAPI:
    """Manages database users and credentials (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self, service_id: str) -> List[DatabaseUser]:
        """List all database users for a service."""
        data = self._http.get(f"/managed-services/{service_id}/database-users")
        return [DatabaseUser.from_dict(u) for u in data.get("users", [])]

    def reveal_password(self, service_id: str, username: str) -> RevealPasswordResponse:
        """Reveal the password and connection string for a database user."""
        data = self._http.post(
            f"/managed-services/{service_id}/database-users/{username}/reveal-password"
        )
        return RevealPasswordResponse.from_dict(data)


class AsyncUsersAPI:
    """Manages database users and credentials (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(self, service_id: str) -> List[DatabaseUser]:
        """List all database users for a service."""
        data = await self._http.get(f"/managed-services/{service_id}/database-users")
        return [DatabaseUser.from_dict(u) for u in data.get("users", [])]

    async def reveal_password(self, service_id: str, username: str) -> RevealPasswordResponse:
        """Reveal the password and connection string for a database user."""
        data = await self._http.post(
            f"/managed-services/{service_id}/database-users/{username}/reveal-password"
        )
        return RevealPasswordResponse.from_dict(data)
