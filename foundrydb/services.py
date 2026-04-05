"""
FoundryDB SDK - Services API (sync and async).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import CreateServiceRequest, DatabaseType, Service, ServicePreset


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
        database_type: DatabaseType,
        version: str,
        plan_name: str,
        zone: str,
        storage_size_gb: int,
        storage_tier: str,
        organization_id: Optional[str] = None,
        node_count: Optional[int] = None,
        auto_failover_enabled: Optional[bool] = None,
        replication_mode: Optional[str] = None,
        encryption_enabled: Optional[bool] = None,
        allowed_cidrs: Optional[List[str]] = None,
        maintenance_window: Optional[str] = None,
        preset: Optional[str] = None,
        is_ephemeral: Optional[bool] = None,
        ttl_hours: Optional[int] = None,
        created_by_agent_id: Optional[str] = None,
        agent_framework: Optional[str] = None,
        agent_purpose: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Service:
        """Create a new managed service.

        Args:
            name: Display name for the service.
            database_type: Engine type. One of: postgresql, mysql, mongodb,
                valkey, kafka, opensearch, mssql.
            version: Engine version string (e.g. "17" for PostgreSQL 17).
            plan_name: Compute plan identifier (e.g. "tier-2").
            zone: Deployment zone (e.g. "se-sto1").
            storage_size_gb: Size of the data disk in gigabytes.
            storage_tier: Storage performance tier ("standard" or "maxiops").
            organization_id: Optional org ID to override the client-level org
                for this request. Sent as ``X-Active-Org-ID`` when provided.
            node_count: Number of database nodes (1 for single-node,
                3 for a typical HA cluster).
            auto_failover_enabled: Enable automatic primary failover.
            replication_mode: Replication strategy (e.g. "async", "sync").
            encryption_enabled: Enable at-rest encryption for data and backups.
            allowed_cidrs: IP CIDRs allowed to connect. Defaults to no
                restrictions when omitted.
            maintenance_window: Preferred maintenance window string.
            preset: Service preset identifier (e.g. "agent-valkey-session").
            is_ephemeral: Mark the service as ephemeral (auto-deleted after TTL).
            ttl_hours: Auto-delete the service after this many hours (1-720).
            created_by_agent_id: Identifier of the AI agent that created
                this service.
            agent_framework: AI agent framework name (e.g. "langchain",
                "crewai", "autogen", "claude").
            agent_purpose: Purpose of the service for the agent (e.g.
                "conversation_history", "session_cache").
            labels: Custom key-value labels for the service.
        """
        req = CreateServiceRequest(
            name=name,
            database_type=database_type,
            version=version,
            plan_name=plan_name,
            zone=zone,
            storage_size_gb=storage_size_gb,
            storage_tier=storage_tier,
            organization_id=organization_id,
            node_count=node_count,
            auto_failover_enabled=auto_failover_enabled,
            replication_mode=replication_mode,
            encryption_enabled=encryption_enabled,
            allowed_cidrs=allowed_cidrs,
            maintenance_window=maintenance_window,
            preset=preset,
            is_ephemeral=is_ephemeral,
            ttl_hours=ttl_hours,
            created_by_agent_id=created_by_agent_id,
            agent_framework=agent_framework,
            agent_purpose=agent_purpose,
            labels=labels,
        )
        body = req.to_dict()
        # Per-request org override takes precedence over the client-level header.
        extra_headers: Dict[str, str] = {}
        if organization_id:
            extra_headers["X-Active-Org-ID"] = organization_id
        data = self._http.post("/managed-services/", body, extra_headers=extra_headers or None)
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

    def list_presets(self) -> List[ServicePreset]:
        """List available service presets."""
        data = self._http.get("/managed-services/presets")
        return [ServicePreset.from_dict(p) for p in data.get("presets", [])]


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
        database_type: DatabaseType,
        version: str,
        plan_name: str,
        zone: str,
        storage_size_gb: int,
        storage_tier: str,
        organization_id: Optional[str] = None,
        node_count: Optional[int] = None,
        auto_failover_enabled: Optional[bool] = None,
        replication_mode: Optional[str] = None,
        encryption_enabled: Optional[bool] = None,
        allowed_cidrs: Optional[List[str]] = None,
        maintenance_window: Optional[str] = None,
        preset: Optional[str] = None,
        is_ephemeral: Optional[bool] = None,
        ttl_hours: Optional[int] = None,
        created_by_agent_id: Optional[str] = None,
        agent_framework: Optional[str] = None,
        agent_purpose: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Service:
        """Create a new managed service.

        Args:
            name: Display name for the service.
            database_type: Engine type. One of: postgresql, mysql, mongodb,
                valkey, kafka, opensearch, mssql.
            version: Engine version string (e.g. "17" for PostgreSQL 17).
            plan_name: Compute plan identifier (e.g. "tier-2").
            zone: Deployment zone (e.g. "se-sto1").
            storage_size_gb: Size of the data disk in gigabytes.
            storage_tier: Storage performance tier ("standard" or "maxiops").
            organization_id: Optional org ID to override the client-level org
                for this request. Sent as ``X-Active-Org-ID`` when provided.
            node_count: Number of database nodes (1 for single-node,
                3 for a typical HA cluster).
            auto_failover_enabled: Enable automatic primary failover.
            replication_mode: Replication strategy (e.g. "async", "sync").
            encryption_enabled: Enable at-rest encryption for data and backups.
            allowed_cidrs: IP CIDRs allowed to connect. Defaults to no
                restrictions when omitted.
            maintenance_window: Preferred maintenance window string.
            preset: Service preset identifier (e.g. "agent-valkey-session").
            is_ephemeral: Mark the service as ephemeral (auto-deleted after TTL).
            ttl_hours: Auto-delete the service after this many hours (1-720).
            created_by_agent_id: Identifier of the AI agent that created
                this service.
            agent_framework: AI agent framework name (e.g. "langchain",
                "crewai", "autogen", "claude").
            agent_purpose: Purpose of the service for the agent (e.g.
                "conversation_history", "session_cache").
            labels: Custom key-value labels for the service.
        """
        req = CreateServiceRequest(
            name=name,
            database_type=database_type,
            version=version,
            plan_name=plan_name,
            zone=zone,
            storage_size_gb=storage_size_gb,
            storage_tier=storage_tier,
            organization_id=organization_id,
            node_count=node_count,
            auto_failover_enabled=auto_failover_enabled,
            replication_mode=replication_mode,
            encryption_enabled=encryption_enabled,
            allowed_cidrs=allowed_cidrs,
            maintenance_window=maintenance_window,
            preset=preset,
            is_ephemeral=is_ephemeral,
            ttl_hours=ttl_hours,
            created_by_agent_id=created_by_agent_id,
            agent_framework=agent_framework,
            agent_purpose=agent_purpose,
            labels=labels,
        )
        body = req.to_dict()
        extra_headers: Dict[str, str] = {}
        if organization_id:
            extra_headers["X-Active-Org-ID"] = organization_id
        data = await self._http.post("/managed-services/", body, extra_headers=extra_headers or None)
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

    async def list_presets(self) -> List[ServicePreset]:
        """List available service presets."""
        data = await self._http.get("/managed-services/presets")
        return [ServicePreset.from_dict(p) for p in data.get("presets", [])]
