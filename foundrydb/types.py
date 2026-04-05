"""
FoundryDB SDK - Python data models and type definitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

# Supported database engine types.
# postgresql: 14, 15, 16, 17, 18
# mysql: 8.4
# mongodb: 6.0, 7.0, 8.0
# valkey: 7.2, 8.0, 8.1, 9.0
# kafka: 3.6, 3.7, 3.8, 3.9, 4.0
# opensearch: 2
# mssql: 4.8
DatabaseType = Literal[
    "postgresql",
    "mysql",
    "mongodb",
    "valkey",
    "kafka",
    "opensearch",
    "mssql",
]


# ---- Organization models ----

@dataclass
class Organization:
    """Represents a FoundryDB organization (personal or team)."""

    id: str
    name: str
    slug: str
    is_personal: bool
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Organization":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            slug=d.get("slug", ""),
            is_personal=d.get("is_personal", False),
            raw=d,
        )


# ---- Service creation request ----

@dataclass
class CreateServiceRequest:
    """Parameters for creating a new managed service."""

    name: str
    database_type: DatabaseType
    version: str
    plan_name: str
    zone: str
    storage_size_gb: int
    storage_tier: str
    organization_id: Optional[str] = None
    node_count: Optional[int] = None
    auto_failover_enabled: Optional[bool] = None
    replication_mode: Optional[str] = None
    encryption_enabled: Optional[bool] = None
    allowed_cidrs: Optional[List[str]] = None
    maintenance_window: Optional[str] = None
    preset: Optional[str] = None
    is_ephemeral: Optional[bool] = None
    ttl_hours: Optional[int] = None
    created_by_agent_id: Optional[str] = None
    agent_framework: Optional[str] = None
    agent_purpose: Optional[str] = None
    labels: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "name": self.name,
            "database_type": self.database_type,
            "version": self.version,
            "plan_name": self.plan_name,
            "zone": self.zone,
            "storage_size_gb": self.storage_size_gb,
            "storage_tier": self.storage_tier,
        }
        if self.node_count is not None:
            body["node_count"] = self.node_count
        if self.auto_failover_enabled is not None:
            body["auto_failover_enabled"] = self.auto_failover_enabled
        if self.replication_mode is not None:
            body["replication_mode"] = self.replication_mode
        if self.encryption_enabled is not None:
            body["encryption_enabled"] = self.encryption_enabled
        if self.allowed_cidrs is not None:
            body["allowed_cidrs"] = self.allowed_cidrs
        if self.maintenance_window is not None:
            body["maintenance_window"] = self.maintenance_window
        if self.preset is not None:
            body["preset"] = self.preset
        if self.is_ephemeral is not None:
            body["is_ephemeral"] = self.is_ephemeral
        if self.ttl_hours is not None:
            body["ttl_hours"] = self.ttl_hours
        if self.created_by_agent_id is not None:
            body["created_by_agent_id"] = self.created_by_agent_id
        if self.agent_framework is not None:
            body["agent_framework"] = self.agent_framework
        if self.agent_purpose is not None:
            body["agent_purpose"] = self.agent_purpose
        if self.labels is not None:
            body["labels"] = self.labels
        return body


# ---- Service models ----

@dataclass
class DNSRecord:
    full_domain: str
    record_type: str
    value: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DNSRecord":
        return cls(
            full_domain=d.get("full_domain", ""),
            record_type=d.get("record_type", ""),
            value=d.get("value", ""),
            raw=d,
        )


@dataclass
class Service:
    id: str
    name: str
    database_type: str
    version: str
    status: str
    plan_name: str
    zone: str
    storage_size_gb: int
    storage_tier: str
    created_at: str
    updated_at: str
    dns_records: List[DNSRecord] = field(default_factory=list)
    allowed_cidrs: List[str] = field(default_factory=list)
    maintenance_window: Optional[str] = None
    is_ephemeral: Optional[bool] = None
    ttl_hours: Optional[int] = None
    scheduled_deletion_at: Optional[str] = None
    preset: Optional[str] = None
    agent_framework: Optional[str] = None
    agent_purpose: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Service":
        dns = [DNSRecord.from_dict(r) for r in d.get("dns_records", [])]
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            database_type=d.get("database_type", ""),
            version=d.get("version", ""),
            status=d.get("status", ""),
            plan_name=d.get("plan_name", ""),
            zone=d.get("zone", ""),
            storage_size_gb=d.get("storage_size_gb", 0),
            storage_tier=d.get("storage_tier", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            dns_records=dns,
            allowed_cidrs=d.get("allowed_cidrs", []),
            maintenance_window=d.get("maintenance_window"),
            is_ephemeral=d.get("is_ephemeral"),
            ttl_hours=d.get("ttl_hours"),
            scheduled_deletion_at=d.get("scheduled_deletion_at"),
            preset=d.get("preset"),
            agent_framework=d.get("agent_framework"),
            agent_purpose=d.get("agent_purpose"),
            labels=d.get("labels"),
            raw=d,
        )


# ---- User / credential models ----

@dataclass
class DatabaseUser:
    username: str
    roles: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DatabaseUser":
        return cls(
            username=d.get("username", ""),
            roles=d.get("roles", []),
            created_at=d.get("created_at"),
            raw=d,
        )


@dataclass
class RevealPasswordResponse:
    username: str
    password: str
    host: str
    port: int
    database: str
    connection_string: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RevealPasswordResponse":
        return cls(
            username=d.get("username", ""),
            password=d.get("password", ""),
            host=d.get("host", ""),
            port=d.get("port", 0),
            database=d.get("database", ""),
            connection_string=d.get("connection_string", ""),
            raw=d,
        )


# ---- Backup models ----

@dataclass
class Backup:
    id: str
    service_id: str
    status: str
    backup_type: str
    size_bytes: Optional[int]
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Backup":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            status=d.get("status", ""),
            backup_type=d.get("backup_type", ""),
            size_bytes=d.get("size_bytes"),
            created_at=d.get("created_at", ""),
            completed_at=d.get("completed_at"),
            error_message=d.get("error_message"),
            raw=d,
        )


@dataclass
class TriggerBackupResponse:
    backup_id: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TriggerBackupResponse":
        return cls(
            backup_id=d.get("backup_id"),
            raw=d,
        )


# ---- Monitoring models ----

@dataclass
class ServiceMetrics:
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    disk_usage_percent: Optional[float]
    connections_active: Optional[int]
    connections_max: Optional[int]
    replication_lag_ms: Optional[float]
    queries_per_second: Optional[float]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ServiceMetrics":
        return cls(
            cpu_usage_percent=d.get("cpu_usage_percent"),
            memory_usage_percent=d.get("memory_usage_percent"),
            disk_usage_percent=d.get("disk_usage_percent"),
            connections_active=d.get("connections_active"),
            connections_max=d.get("connections_max"),
            replication_lag_ms=d.get("replication_lag_ms"),
            queries_per_second=d.get("queries_per_second"),
            raw=d,
        )


@dataclass
class LogsTaskResponse:
    task_id: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LogsTaskResponse":
        return cls(task_id=d.get("task_id", ""))


@dataclass
class LogsResultResponse:
    status: str
    logs: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LogsResultResponse":
        return cls(
            status=d.get("status", ""),
            logs=d.get("logs", ""),
        )


# ---- Preset models ----

@dataclass
class ServicePreset:
    """A predefined service configuration template."""

    id: str
    name: str
    description: str
    database_type: str
    default_version: str
    default_plan: str
    default_storage_gb: int
    default_storage_tier: str
    config_template_id: Optional[str] = None
    is_ephemeral: Optional[bool] = None
    default_ttl_hours: Optional[int] = None
    node_count: Optional[int] = None
    replication_mode: Optional[str] = None
    extensions: List[str] = field(default_factory=list)
    recommended_features: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ServicePreset":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            database_type=d.get("database_type", ""),
            default_version=d.get("default_version", ""),
            default_plan=d.get("default_plan", ""),
            default_storage_gb=d.get("default_storage_gb", 0),
            default_storage_tier=d.get("default_storage_tier", ""),
            config_template_id=d.get("config_template_id"),
            is_ephemeral=d.get("is_ephemeral"),
            default_ttl_hours=d.get("default_ttl_hours"),
            node_count=d.get("node_count"),
            replication_mode=d.get("replication_mode"),
            extensions=d.get("extensions", []),
            recommended_features=d.get("recommended_features", []),
            tags=d.get("tags", []),
            raw=d,
        )


# ---- Error types ----

class FoundryDBError(Exception):
    """Raised when the FoundryDB API returns a non-2xx response."""

    def __init__(self, message: str, status_code: int, body: Dict[str, Any]) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def __repr__(self) -> str:
        return f"FoundryDBError(status_code={self.status_code}, message={str(self)!r})"
