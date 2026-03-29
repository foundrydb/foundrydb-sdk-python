"""
FoundryDB SDK - Services API (sync and async).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import Service


class ServicesAPI:
    """Manages FoundryDB managed services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self) -> List[Service]:
        """List all managed services."""
        data = self._http.get("/managed-services/")
        return [Service.from_dict(s) for s in data.get("services", [])]

    def create(
        self,
        *,
        name: str,
        database_type: str,
        version: str,
        plan_name: str,
        zone: str,
        storage_size_gb: int,
        storage_tier: str,
        allowed_cidrs: Optional[List[str]] = None,
        maintenance_window: Optional[str] = None,
    ) -> Service:
        """Create a new managed service."""
        body: Dict[str, Any] = {
            "name": name,
            "database_type": database_type,
            "version": version,
            "plan_name": plan_name,
            "zone": zone,
            "storage_size_gb": storage_size_gb,
            "storage_tier": storage_tier,
        }
        if allowed_cidrs is not None:
            body["allowed_cidrs"] = allowed_cidrs
        if maintenance_window is not None:
            body["maintenance_window"] = maintenance_window
        data = self._http.post("/managed-services/", body)
        return Service.from_dict(data)

    def get(self, service_id: str) -> Service:
        """Get a specific managed service by ID."""
        data = self._http.get(f"/managed-services/{service_id}")
        return Service.from_dict(data)

    def update(
        self,
        service_id: str,
        *,
        name: Optional[str] = None,
        allowed_cidrs: Optional[List[str]] = None,
        maintenance_window: Optional[str] = None,
        plan_name: Optional[str] = None,
        storage_size_gb: Optional[int] = None,
    ) -> Service:
        """Update a managed service."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if allowed_cidrs is not None:
            body["allowed_cidrs"] = allowed_cidrs
        if maintenance_window is not None:
            body["maintenance_window"] = maintenance_window
        if plan_name is not None:
            body["plan_name"] = plan_name
        if storage_size_gb is not None:
            body["storage_size_gb"] = storage_size_gb
        data = self._http.patch(f"/managed-services/{service_id}", body)
        return Service.from_dict(data)

    def delete(self, service_id: str) -> None:
        """Delete a managed service."""
        self._http.delete(f"/managed-services/{service_id}")


class AsyncServicesAPI:
    """Manages FoundryDB managed services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(self) -> List[Service]:
        """List all managed services."""
        data = await self._http.get("/managed-services/")
        return [Service.from_dict(s) for s in data.get("services", [])]

    async def create(
        self,
        *,
        name: str,
        database_type: str,
        version: str,
        plan_name: str,
        zone: str,
        storage_size_gb: int,
        storage_tier: str,
        allowed_cidrs: Optional[List[str]] = None,
        maintenance_window: Optional[str] = None,
    ) -> Service:
        """Create a new managed service."""
        body: Dict[str, Any] = {
            "name": name,
            "database_type": database_type,
            "version": version,
            "plan_name": plan_name,
            "zone": zone,
            "storage_size_gb": storage_size_gb,
            "storage_tier": storage_tier,
        }
        if allowed_cidrs is not None:
            body["allowed_cidrs"] = allowed_cidrs
        if maintenance_window is not None:
            body["maintenance_window"] = maintenance_window
        data = await self._http.post("/managed-services/", body)
        return Service.from_dict(data)

    async def get(self, service_id: str) -> Service:
        """Get a specific managed service by ID."""
        data = await self._http.get(f"/managed-services/{service_id}")
        return Service.from_dict(data)

    async def update(
        self,
        service_id: str,
        *,
        name: Optional[str] = None,
        allowed_cidrs: Optional[List[str]] = None,
        maintenance_window: Optional[str] = None,
        plan_name: Optional[str] = None,
        storage_size_gb: Optional[int] = None,
    ) -> Service:
        """Update a managed service."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if allowed_cidrs is not None:
            body["allowed_cidrs"] = allowed_cidrs
        if maintenance_window is not None:
            body["maintenance_window"] = maintenance_window
        if plan_name is not None:
            body["plan_name"] = plan_name
        if storage_size_gb is not None:
            body["storage_size_gb"] = storage_size_gb
        data = await self._http.patch(f"/managed-services/{service_id}", body)
        return Service.from_dict(data)

    async def delete(self, service_id: str) -> None:
        """Delete a managed service."""
        await self._http.delete(f"/managed-services/{service_id}")
