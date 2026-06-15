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


# ---- App service models ----

@dataclass
class AppContainerConfig:
    """Container configuration for an app service."""

    image_ref: str
    container_port: int
    env: Optional[Dict[str, str]] = None
    custom_domains: Optional[List[str]] = None
    registry_username: Optional[str] = None
    health_check_path: Optional[str] = None
    health_check_interval_seconds: Optional[int] = None
    health_check_timeout_seconds: Optional[int] = None
    health_check_healthy_threshold: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppContainerConfig":
        return cls(
            image_ref=d.get("image_ref", ""),
            container_port=d.get("container_port", 0),
            env=d.get("env"),
            custom_domains=d.get("custom_domains"),
            registry_username=d.get("registry_username"),
            health_check_path=d.get("health_check_path"),
            health_check_interval_seconds=d.get("health_check_interval_seconds"),
            health_check_timeout_seconds=d.get("health_check_timeout_seconds"),
            health_check_healthy_threshold=d.get("health_check_healthy_threshold"),
            raw=d,
        )

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "image_ref": self.image_ref,
            "container_port": self.container_port,
        }
        if self.env is not None:
            body["env"] = self.env
        if self.custom_domains is not None:
            body["custom_domains"] = self.custom_domains
        if self.registry_username is not None:
            body["registry_username"] = self.registry_username
        if self.health_check_path is not None:
            body["health_check_path"] = self.health_check_path
        if self.health_check_interval_seconds is not None:
            body["health_check_interval_seconds"] = self.health_check_interval_seconds
        if self.health_check_timeout_seconds is not None:
            body["health_check_timeout_seconds"] = self.health_check_timeout_seconds
        if self.health_check_healthy_threshold is not None:
            body["health_check_healthy_threshold"] = self.health_check_healthy_threshold
        return body


@dataclass
class ServiceAttachment:
    """A database or app attached to an app service."""

    id: str
    attached_service_id: str
    status: str
    env_prefix: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ServiceAttachment":
        return cls(
            id=d.get("id", ""),
            attached_service_id=d.get("attached_service_id", ""),
            status=d.get("status", ""),
            env_prefix=d.get("env_prefix"),
            error_message=d.get("error_message"),
            raw=d,
        )


@dataclass
class AppService:
    """A container app hosted on the platform."""

    id: str
    name: str
    service_kind: str
    status: str
    zone: str
    plan_name: str
    storage_size_gb: int
    created_at: str
    updated_at: str
    app_config: Optional[AppContainerConfig] = None
    url: Optional[str] = None
    attachments: List[ServiceAttachment] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppService":
        cfg = AppContainerConfig.from_dict(d["app_config"]) if d.get("app_config") else None
        attachments = [ServiceAttachment.from_dict(a) for a in d.get("attachments", [])]
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            service_kind=d.get("service_kind", "app"),
            status=d.get("status", ""),
            zone=d.get("zone", ""),
            plan_name=d.get("plan_name", ""),
            storage_size_gb=d.get("storage_size_gb", 0),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            app_config=cfg,
            url=d.get("url"),
            attachments=attachments,
            raw=d,
        )


# ---- Auth models ----

@dataclass
class SmtpConfig:
    """SMTP credentials for magic-link email delivery.

    Write-only at the API boundary: accepted on enable, stored in the platform
    secret store, and never returned in any response.
    """

    host: str
    port: int
    username: str
    password: str
    from_address: str
    from_name: Optional[str] = None
    insecure_skip_verify: bool = False

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "from_address": self.from_address,
        }
        if self.from_name is not None:
            body["from_name"] = self.from_name
        if self.insecure_skip_verify:
            body["insecure_skip_verify"] = self.insecure_skip_verify
        return body


@dataclass
class AuthTheme:
    """Non-PII branding applied to the hosted login pages."""

    display_name: Optional[str] = None
    brand_color: Optional[str] = None
    logo_url: Optional[str] = None
    support_url: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuthTheme":
        return cls(
            display_name=d.get("display_name"),
            brand_color=d.get("brand_color"),
            logo_url=d.get("logo_url"),
            support_url=d.get("support_url"),
            raw=d,
        )

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if self.display_name is not None:
            body["display_name"] = self.display_name
        if self.brand_color is not None:
            body["brand_color"] = self.brand_color
        if self.logo_url is not None:
            body["logo_url"] = self.logo_url
        if self.support_url is not None:
            body["support_url"] = self.support_url
        return body


@dataclass
class IdpProviderRequest:
    """One social-login provider supplied at enable time.

    The ``client_secret`` is write-only: stored in the platform secret store
    and never returned in any response.
    """

    provider: str
    client_id: str
    client_secret: str
    display_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "provider": self.provider,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.display_name is not None:
            body["display_name"] = self.display_name
        return body


@dataclass
class IdpProviderConfig:
    """Stored, non-secret configuration of one social-login provider.

    Returned as part of ``AuthConfiguration``. The ``client_secret`` is never
    returned; it is custodied in the platform secret store.
    """

    provider: str
    client_id: str
    display_name: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IdpProviderConfig":
        return cls(
            provider=d.get("provider", ""),
            client_id=d.get("client_id", ""),
            display_name=d.get("display_name"),
            raw=d,
        )


@dataclass
class AuthEnableRequest:
    """Parameters for enabling end-user authentication on an app service.

    ``attachment_id`` must reference a healthy PostgreSQL attachment of the app.
    ``issuer_domain_choice`` is fixed at enable time: ``"fallback"`` uses a
    platform subdomain; ``"custom"`` uses your own domain.
    ``smtp`` is mandatory and write-only. ``idp_providers`` optionally enables
    social login (Google and GitHub).
    """

    attachment_id: str
    issuer_domain_choice: str
    smtp: SmtpConfig
    theme: Optional[AuthTheme] = None
    idp_providers: Optional[List[IdpProviderRequest]] = None

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "attachment_id": self.attachment_id,
            "issuer_domain_choice": self.issuer_domain_choice,
            "smtp": self.smtp.to_dict(),
        }
        if self.theme is not None:
            body["theme"] = self.theme.to_dict()
        if self.idp_providers:
            body["idp_providers"] = [p.to_dict() for p in self.idp_providers]
        return body


@dataclass
class AuthConfiguration:
    """Auth enablement record for an app service.

    Holds enablement state only. The end-user identity data lives in the
    customer's own PostgreSQL database. Secret custody locations are never
    serialized.
    """

    id: str
    app_service_id: str
    database_service_id: str
    attachment_id: str
    issuer_url: str
    fallback_domain: str
    status: str
    theme: Optional[AuthTheme] = None
    idp_providers: List[IdpProviderConfig] = field(default_factory=list)
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    custom_domain: Optional[str] = None
    schema_version_applied: Optional[str] = None
    failure_reason: Optional[str] = None
    auth_app_service_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuthConfiguration":
        theme_raw = d.get("theme")
        theme = AuthTheme.from_dict(theme_raw) if theme_raw else None
        idp_providers = [IdpProviderConfig.from_dict(p) for p in d.get("idp_providers", [])]
        return cls(
            id=d.get("id", ""),
            app_service_id=d.get("app_service_id", ""),
            database_service_id=d.get("database_service_id", ""),
            attachment_id=d.get("attachment_id", ""),
            issuer_url=d.get("issuer_url", ""),
            fallback_domain=d.get("fallback_domain", ""),
            status=d.get("status", ""),
            theme=theme,
            idp_providers=idp_providers,
            user_id=d.get("user_id"),
            organization_id=d.get("organization_id"),
            custom_domain=d.get("custom_domain"),
            schema_version_applied=d.get("schema_version_applied"),
            failure_reason=d.get("failure_reason"),
            auth_app_service_id=d.get("auth_app_service_id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            raw=d,
        )


@dataclass
class AuthSigningKey:
    """Controller-side record of one JWT signing keypair.

    Key material is held in the platform secret store and never returned.
    Only the key id, algorithm, and lifecycle status are exposed.
    """

    id: str
    auth_configuration_id: str
    kid: str
    algorithm: str
    status: str
    activated_at: Optional[str] = None
    retired_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuthSigningKey":
        return cls(
            id=d.get("id", ""),
            auth_configuration_id=d.get("auth_configuration_id", ""),
            kid=d.get("kid", ""),
            algorithm=d.get("algorithm", ""),
            status=d.get("status", ""),
            activated_at=d.get("activated_at"),
            retired_at=d.get("retired_at"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            raw=d,
        )


@dataclass
class AuthConfigurationWithKeys:
    """Auth configuration and its signing key records."""

    auth: Optional[AuthConfiguration]
    signing_keys: List[AuthSigningKey] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuthConfigurationWithKeys":
        auth_raw = d.get("auth")
        auth = AuthConfiguration.from_dict(auth_raw) if auth_raw else None
        signing_keys = [AuthSigningKey.from_dict(k) for k in d.get("signing_keys", [])]
        return cls(auth=auth, signing_keys=signing_keys, raw=d)


# ---- Error types ----

class FoundryDBError(Exception):
    """Raised when the FoundryDB API returns a non-2xx response."""

    def __init__(self, message: str, status_code: int, body: Dict[str, Any]) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def __repr__(self) -> str:
        return f"FoundryDBError(status_code={self.status_code}, message={str(self)!r})"
