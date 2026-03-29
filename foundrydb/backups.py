"""
FoundryDB SDK - Backups API (sync and async).
"""
from __future__ import annotations

from typing import List

from .client import HTTPClient, AsyncHTTPClient
from .types import Backup, TriggerBackupResponse


class BackupsAPI:
    """Manages backups for a service (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self, service_id: str) -> List[Backup]:
        """List all backups for a service."""
        data = self._http.get(f"/managed-services/{service_id}/backups")
        return [Backup.from_dict(b) for b in data.get("backups", [])]

    def trigger(self, service_id: str) -> TriggerBackupResponse:
        """Trigger an on-demand backup for a service."""
        data = self._http.post(f"/managed-services/{service_id}/backups")
        return TriggerBackupResponse.from_dict(data or {})


class AsyncBackupsAPI:
    """Manages backups for a service (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(self, service_id: str) -> List[Backup]:
        """List all backups for a service."""
        data = await self._http.get(f"/managed-services/{service_id}/backups")
        return [Backup.from_dict(b) for b in data.get("backups", [])]

    async def trigger(self, service_id: str) -> TriggerBackupResponse:
        """Trigger an on-demand backup for a service."""
        data = await self._http.post(f"/managed-services/{service_id}/backups")
        return TriggerBackupResponse.from_dict(data or {})
