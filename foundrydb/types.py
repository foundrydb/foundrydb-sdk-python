"""
FoundryDB SDK - Python data models and type definitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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


# ---- Error types ----

class FoundryDBError(Exception):
    """Raised when the FoundryDB API returns a non-2xx response."""

    def __init__(self, message: str, status_code: int, body: Dict[str, Any]) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def __repr__(self) -> str:
        return f"FoundryDBError(status_code={self.status_code}, message={str(self)!r})"
