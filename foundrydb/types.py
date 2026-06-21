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


@dataclass
class AppDeployStep:
    """One phase of an app deploy or redeploy, captured on the agent.

    ``status`` is one of ``"ok"``, ``"failed"``, or ``"info"``.
    ``duration_ms`` is omitted when the step has not yet completed.
    """

    step: str
    status: str
    started_at: str
    message: Optional[str] = None
    detail: Optional[str] = None
    duration_ms: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppDeployStep":
        return cls(
            step=d.get("step", ""),
            status=d.get("status", ""),
            started_at=d.get("started_at", ""),
            message=d.get("message"),
            detail=d.get("detail"),
            duration_ms=d.get("duration_ms"),
            raw=d,
        )


@dataclass
class AppDeployment:
    """A single revision in an app service's deploy history.

    The newest entry reflects the currently serving container. Pass an older
    entry's ``id`` to ``rollback`` to redeploy it.
    ``deploy_logs`` is the ordered list of deploy steps the agent executed for
    this revision (image start, health probe, ingress cutover, previous-color
    teardown). It is distinct from runtime container logs and is empty for
    revisions deployed before the platform captured deploy steps.
    """

    id: str
    service_id: str
    image_ref: str
    container_port: int
    created_at: str
    env: Optional[Dict[str, str]] = None
    custom_domains: Optional[List[str]] = None
    registry_username: Optional[str] = None
    reason: Optional[str] = None
    deploy_logs: List[AppDeployStep] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppDeployment":
        logs = [AppDeployStep.from_dict(s) for s in d.get("deploy_logs", [])]
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            image_ref=d.get("image_ref", ""),
            container_port=d.get("container_port", 0),
            created_at=d.get("created_at", ""),
            env=d.get("env"),
            custom_domains=d.get("custom_domains"),
            registry_username=d.get("registry_username"),
            reason=d.get("reason"),
            deploy_logs=logs,
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


# ---- Edge gateway models ----

# Lifecycle of a customer custom domain on the edge tier.
EdgeDomainStatus = Literal[
    "pending_verification",
    "verifying",
    "issuing_certificate",
    "propagating",
    "active",
    "failed",
    "deleting",
]

# How the edge web application firewall treats matching requests.
EdgeWAFMode = Literal["off", "detect"]

# What an edge rate-limit bucket is keyed on.
EdgeRateLimitKey = Literal["ip", "api_key"]


@dataclass
class EdgeDomain:
    """A customer custom domain attached to an app service, served through
    the edge tier. Created in pending_verification status; the platform
    verifies DNS ownership and then provisions a TLS certificate."""

    id: str
    service_id: str
    user_id: str
    domain: str
    status: EdgeDomainStatus
    cname_target: str
    created_at: str
    updated_at: str
    certificate_id: Optional[str] = None
    verification_checked_at: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EdgeDomain":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            user_id=d.get("user_id", ""),
            domain=d.get("domain", ""),
            status=d.get("status", ""),
            cname_target=d.get("cname_target", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            certificate_id=d.get("certificate_id"),
            verification_checked_at=d.get("verification_checked_at"),
            error_message=d.get("error_message"),
            raw=d,
        )


@dataclass
class EdgeCacheRule:
    """Caches responses under one path prefix for a fixed TTL."""

    path_prefix: str
    ttl_seconds: int

    def to_dict(self) -> Dict[str, Any]:
        return {"path_prefix": self.path_prefix, "ttl_seconds": self.ttl_seconds}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EdgeCacheRule":
        return cls(
            path_prefix=d.get("path_prefix", ""),
            ttl_seconds=d.get("ttl_seconds", 0),
        )


@dataclass
class EdgeRateLimit:
    """Token bucket enforced per PoP at the edge."""

    requests_per_second: int
    burst: int
    key: EdgeRateLimitKey

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requests_per_second": self.requests_per_second,
            "burst": self.burst,
            "key": self.key,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EdgeRateLimit":
        return cls(
            requests_per_second=d.get("requests_per_second", 0),
            burst=d.get("burst", 0),
            key=d.get("key", "ip"),
        )


@dataclass
class EdgeAppApplication:
    """One PoP's convergence state for an app service."""

    zone: str
    applied_version: int
    status: str
    error_message: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EdgeAppApplication":
        return cls(
            zone=d.get("zone", ""),
            applied_version=d.get("applied_version", 0),
            status=d.get("status", ""),
            error_message=d.get("error_message", ""),
            raw=d,
        )


@dataclass
class EdgeStatus:
    """Edge overview for an app service: whether the edge tier is enabled,
    the home PoP, CNAME target, desired-state version, and per-PoP
    convergence status."""

    edge_enabled: bool
    config_version: int
    home_pop: str = ""
    cname_target: str = ""
    applications: List[EdgeAppApplication] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EdgeStatus":
        apps = [EdgeAppApplication.from_dict(a) for a in d.get("applications") or []]
        return cls(
            edge_enabled=d.get("edge_enabled", False),
            config_version=d.get("config_version", 0),
            home_pop=d.get("home_pop", ""),
            cname_target=d.get("cname_target", ""),
            applications=apps,
            raw=d,
        )


@dataclass
class EdgeSettings:
    """Customer-tunable edge settings echoed back after an update. Domains
    and origin are platform-derived and are not included here."""

    waf_mode: EdgeWAFMode
    config_version: int
    cache_rules: Optional[List[EdgeCacheRule]] = None
    rate_limit: Optional[EdgeRateLimit] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EdgeSettings":
        rules_data = d.get("cache_rules")
        rules = [EdgeCacheRule.from_dict(r) for r in rules_data] if rules_data else None
        rl_data = d.get("rate_limit")
        rate_limit = EdgeRateLimit.from_dict(rl_data) if rl_data else None
        return cls(
            waf_mode=d.get("waf_mode", "off"),
            config_version=d.get("config_version", 0),
            cache_rules=rules,
            rate_limit=rate_limit,
            raw=d,
        )


# ---- App jobs models ----

@dataclass
class AppJob:
    """A job definition on an app service: a container run with an optional
    cron schedule. A ``None`` schedule_cron means the job only runs when
    invoked explicitly via run()."""

    id: str
    service_id: str
    name: str
    timezone: str
    enabled: bool
    max_retries: int
    retry_backoff_seconds: int
    max_runtime_seconds: int
    concurrency_cap: int
    overlap_policy: str
    created_at: str
    updated_at: str
    schedule_cron: Optional[str] = None
    image_ref: Optional[str] = None
    command: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    next_run_at: Optional[str] = None
    last_run_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppJob":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            name=d.get("name", ""),
            timezone=d.get("timezone", "UTC"),
            enabled=d.get("enabled", True),
            max_retries=d.get("max_retries", 0),
            retry_backoff_seconds=d.get("retry_backoff_seconds", 0),
            max_runtime_seconds=d.get("max_runtime_seconds", 3600),
            concurrency_cap=d.get("concurrency_cap", 1),
            overlap_policy=d.get("overlap_policy", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            schedule_cron=d.get("schedule_cron"),
            image_ref=d.get("image_ref"),
            command=d.get("command"),
            env=d.get("env"),
            next_run_at=d.get("next_run_at"),
            last_run_at=d.get("last_run_at"),
            raw=d,
        )


@dataclass
class AppJobInvocation:
    """One execution (or recorded skip) of an app job.

    ``status`` is one of queued, running, succeeded, failed, timed_out, or
    skipped.
    """

    id: str
    job_id: str
    service_id: str
    status: str
    attempt: int
    triggered_by: str
    queued_at: str
    created_at: str
    updated_at: str
    triggered_by_user_id: Optional[str] = None
    agent_task_id: Optional[str] = None
    unit_name: Optional[str] = None
    scheduled_for: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    log_tail: Optional[str] = None
    retry_enqueued: bool = False
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppJobInvocation":
        return cls(
            id=d.get("id", ""),
            job_id=d.get("job_id", ""),
            service_id=d.get("service_id", ""),
            status=d.get("status", ""),
            attempt=d.get("attempt", 0),
            triggered_by=d.get("triggered_by", ""),
            queued_at=d.get("queued_at", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            triggered_by_user_id=d.get("triggered_by_user_id"),
            agent_task_id=d.get("agent_task_id"),
            unit_name=d.get("unit_name"),
            scheduled_for=d.get("scheduled_for"),
            started_at=d.get("started_at"),
            finished_at=d.get("finished_at"),
            duration_ms=d.get("duration_ms"),
            exit_code=d.get("exit_code"),
            error_message=d.get("error_message"),
            log_tail=d.get("log_tail"),
            retry_enqueued=d.get("retry_enqueued", False),
            raw=d,
        )


@dataclass
class AppJobLogLines:
    """Log payload inside a completed invocation logs fetch."""

    lines: List[str]
    log_file_path: str
    truncated_at: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppJobLogLines":
        return cls(
            lines=d.get("lines", []),
            log_file_path=d.get("log_file_path", ""),
            truncated_at=d.get("truncated_at"),
            raw=d,
        )


@dataclass
class AppJobInvocationLogs:
    """Poll response for an invocation logs fetch task.

    ``status`` mirrors the agent task lifecycle (PENDING, DISPATCHED,
    IN_PROGRESS, COMPLETED, FAILED, TIMEOUT, CANCELLED). ``result`` is set
    once COMPLETED.
    """

    task_id: str
    status: str
    result: Optional[AppJobLogLines] = None
    error_message: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AppJobInvocationLogs":
        result_raw = d.get("result")
        return cls(
            task_id=d.get("task_id", ""),
            status=d.get("status", ""),
            result=AppJobLogLines.from_dict(result_raw) if result_raw else None,
            error_message=d.get("error_message", ""),
            raw=d,
        )


# ---- Queue models ----

@dataclass
class Queue:
    """A named message queue hosted on a PostgreSQL managed service.

    Status is one of Pending, Provisioning, Active, Deprovisioning, or
    Failed. Brokered data-plane operations require Active status.
    """

    id: str
    service_id: str
    name: str
    database_name: str
    visibility_timeout_seconds: int
    max_attempts: int
    dlq_enabled: bool
    status: str
    created_at: str
    updated_at: str
    user_id: str = ""
    organization_id: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Queue":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            name=d.get("name", ""),
            database_name=d.get("database_name", ""),
            visibility_timeout_seconds=d.get("visibility_timeout_seconds", 30),
            max_attempts=d.get("max_attempts", 5),
            dlq_enabled=d.get("dlq_enabled", True),
            status=d.get("status", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            user_id=d.get("user_id", ""),
            organization_id=d.get("organization_id"),
            error_message=d.get("error_message"),
            raw=d,
        )


@dataclass
class QueueEnqueueMessageIDs:
    """Assigned message IDs from a completed enqueue task, in request order."""

    message_ids: List[int]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QueueEnqueueMessageIDs":
        return cls(message_ids=d.get("message_ids", []), raw=d)


@dataclass
class QueueEnqueueResult:
    """Poll response for an enqueue task.

    ``status`` mirrors the agent task lifecycle. ``result`` is set once
    COMPLETED.
    """

    task_id: str
    status: str
    result: Optional[QueueEnqueueMessageIDs] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QueueEnqueueResult":
        result_raw = d.get("result")
        return cls(
            task_id=d.get("task_id", ""),
            status=d.get("status", ""),
            result=QueueEnqueueMessageIDs.from_dict(result_raw) if result_raw else None,
            raw=d,
        )


@dataclass
class QueueStats:
    """Per-queue depth snapshot."""

    queue_name: str
    ready_messages: int
    inflight_messages: int
    dead_messages: int
    oldest_age_seconds: float
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QueueStats":
        return cls(
            queue_name=d.get("queue_name", ""),
            ready_messages=d.get("ready_messages", 0),
            inflight_messages=d.get("inflight_messages", 0),
            dead_messages=d.get("dead_messages", 0),
            oldest_age_seconds=d.get("oldest_age_seconds", 0.0),
            raw=d,
        )


@dataclass
class QueueStatsResult:
    """Poll response for a queue stats task."""

    task_id: str
    status: str
    result: Optional[QueueStats] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QueueStatsResult":
        result_raw = d.get("result")
        return cls(
            task_id=d.get("task_id", ""),
            status=d.get("status", ""),
            result=QueueStats.from_dict(result_raw) if result_raw else None,
            raw=d,
        )


# ---- File service models ----

@dataclass
class FilesBucket:
    """One bucket backing a files service."""

    region: str
    bucket: str
    endpoint: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesBucket":
        return cls(
            region=d.get("region", ""),
            bucket=d.get("bucket", ""),
            endpoint=d.get("endpoint", ""),
            raw=d,
        )


@dataclass
class FilesConfig:
    """Per-service configuration of a files service."""

    buckets: List[FilesBucket]
    quota_gb_soft: int
    quota_gb_hard: int
    versioning: bool
    sse: bool
    lifecycle_enabled: bool
    measured_bytes: int
    over_quota: bool
    measured_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesConfig":
        return cls(
            buckets=[FilesBucket.from_dict(b) for b in d.get("buckets", [])],
            quota_gb_soft=d.get("quota_gb_soft", 0),
            quota_gb_hard=d.get("quota_gb_hard", 0),
            versioning=d.get("versioning", False),
            sse=d.get("sse", False),
            lifecycle_enabled=d.get("lifecycle_enabled", False),
            measured_bytes=d.get("measured_bytes", 0),
            over_quota=d.get("over_quota", False),
            measured_at=d.get("measured_at"),
            raw=d,
        )


@dataclass
class FilesService:
    """A managed S3-compatible bucket service."""

    id: str
    name: str
    service_kind: str
    status: str
    zone: str
    created_at: str
    updated_at: str
    user_id: str = ""
    organization_id: Optional[str] = None
    files_config: Optional[FilesConfig] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesService":
        cfg_raw = d.get("files_config")
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            service_kind=d.get("service_kind", "files"),
            status=d.get("status", ""),
            zone=d.get("zone", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            user_id=d.get("user_id", ""),
            organization_id=d.get("organization_id"),
            files_config=FilesConfig.from_dict(cfg_raw) if cfg_raw else None,
            raw=d,
        )


@dataclass
class FilesAccessKey:
    """One scoped S3 credential for a files service.

    Only the public half (access_key_id) is returned in list and get
    operations. The secret is returned exactly once at creation time.
    """

    id: str
    service_id: str
    name: str
    access_key_id: str
    prefix: str
    permissions: str
    purpose: str
    status: str
    created_at: str
    updated_at: str
    user_id: str = ""
    organization_id: Optional[str] = None
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesAccessKey":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            name=d.get("name", ""),
            access_key_id=d.get("access_key_id", ""),
            prefix=d.get("prefix", ""),
            permissions=d.get("permissions", "readwrite"),
            purpose=d.get("purpose", "user"),
            status=d.get("status", "active"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            user_id=d.get("user_id", ""),
            organization_id=d.get("organization_id"),
            last_used_at=d.get("last_used_at"),
            revoked_at=d.get("revoked_at"),
            raw=d,
        )


@dataclass
class FilesAccessKeyWithSecret:
    """CreateFilesAccessKey response. The secret is returned exactly once."""

    key: FilesAccessKey
    secret_access_key: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesAccessKeyWithSecret":
        return cls(
            key=FilesAccessKey.from_dict(d),
            secret_access_key=d.get("secret_access_key", ""),
            raw=d,
        )


@dataclass
class FilesPresignedURL:
    """A presigned S3 URL and its validity window."""

    url: str
    method: str
    expires_at: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesPresignedURL":
        return cls(
            url=d.get("url", ""),
            method=d.get("method", ""),
            expires_at=d.get("expires_at", ""),
            raw=d,
        )


@dataclass
class FilesObject:
    """One object in a bucket listing."""

    key: str
    size: int
    last_modified: str
    etag: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesObject":
        return cls(
            key=d.get("key", ""),
            size=d.get("size", 0),
            last_modified=d.get("last_modified", ""),
            etag=d.get("etag", ""),
            raw=d,
        )


@dataclass
class FilesObjectPage:
    """One page of a bucket listing. ``next_cursor`` is non-empty when more
    objects follow; pass it as the cursor of the next call."""

    objects: List[FilesObject]
    next_cursor: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FilesObjectPage":
        return cls(
            objects=[FilesObject.from_dict(o) for o in d.get("objects", [])],
            next_cursor=d.get("next_cursor", ""),
            raw=d,
        )


# ---- Inference models ----

@dataclass
class InferenceProviderConfig:
    """API view of one configured AI provider for an organization.

    The provider API key is never returned; ``has_api_key`` only indicates
    its presence.
    """

    id: str
    provider: str
    eu_endpoint: bool
    enabled: bool
    has_api_key: bool
    eu_resident: bool
    created_at: str
    updated_at: str
    base_url: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InferenceProviderConfig":
        return cls(
            id=d.get("id", ""),
            provider=d.get("provider", ""),
            eu_endpoint=d.get("eu_endpoint", False),
            enabled=d.get("enabled", True),
            has_api_key=d.get("has_api_key", False),
            eu_resident=d.get("eu_resident", False),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            base_url=d.get("base_url"),
            raw=d,
        )


@dataclass
class InferenceKey:
    """API view of a data-plane inference key.

    The secret is never returned after creation. ``key_prefix`` identifies
    the key in customer code.
    """

    id: str
    name: str
    key_prefix: str
    monthly_token_limit: int
    rate_limit_rpm: int
    status: str
    tokens_used_cycle: int
    cycle_month: str
    created_at: str
    revoked_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InferenceKey":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            key_prefix=d.get("key_prefix", ""),
            monthly_token_limit=d.get("monthly_token_limit", 0),
            rate_limit_rpm=d.get("rate_limit_rpm", 0),
            status=d.get("status", ""),
            tokens_used_cycle=d.get("tokens_used_cycle", 0),
            cycle_month=d.get("cycle_month", ""),
            created_at=d.get("created_at", ""),
            revoked_at=d.get("revoked_at"),
            raw=d,
        )


@dataclass
class CreateInferenceKeyResult:
    """Response from creating an inference key. The secret is shown exactly
    once; store it immediately."""

    key: InferenceKey
    secret: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CreateInferenceKeyResult":
        key_raw = d.get("key", d)
        return cls(
            key=InferenceKey.from_dict(key_raw),
            secret=d.get("secret", ""),
            raw=d,
        )


@dataclass
class OrgInferenceSettings:
    """Org-wide inference proxy policy: EU-only routing and cost circuit
    breaker."""

    organization_id: str
    eu_only: bool
    monthly_cost_limit_cents: int
    circuit_open: bool
    updated_at: str
    circuit_opened_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OrgInferenceSettings":
        return cls(
            organization_id=d.get("organization_id", ""),
            eu_only=d.get("eu_only", False),
            monthly_cost_limit_cents=d.get("monthly_cost_limit_cents", 0),
            circuit_open=d.get("circuit_open", False),
            updated_at=d.get("updated_at", ""),
            circuit_opened_at=d.get("circuit_opened_at"),
            raw=d,
        )


@dataclass
class InferenceUsageRow:
    """One aggregated usage row. ``group_key`` is the model name or key id
    depending on the requested grouping."""

    group_key: str
    provider: str
    calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_microcents: int
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InferenceUsageRow":
        return cls(
            group_key=d.get("group_key", ""),
            provider=d.get("provider", ""),
            calls=d.get("calls", 0),
            input_tokens=d.get("input_tokens", 0),
            output_tokens=d.get("output_tokens", 0),
            total_tokens=d.get("total_tokens", 0),
            cost_microcents=d.get("cost_microcents", 0),
            raw=d,
        )


@dataclass
class InferenceUsageSummary:
    """Aggregated inference usage for an organization."""

    from_: str
    to: str
    group_by: str
    rows: List[InferenceUsageRow]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InferenceUsageSummary":
        return cls(
            from_=d.get("from", ""),
            to=d.get("to", ""),
            group_by=d.get("group_by", ""),
            rows=[InferenceUsageRow.from_dict(r) for r in d.get("rows", [])],
            raw=d,
        )


# ---- Webhook and event models ----

@dataclass
class WebhookEndpoint:
    """A customer-configured HTTP endpoint that receives signed event
    notifications. The signing secret is returned only on creation."""

    id: str
    url: str
    events: List[str]
    active: bool
    consecutive_failures: int
    total_delivered: int
    total_failed: int
    created_at: str
    updated_at: str
    secret: str = ""
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    disabled_at: Optional[str] = None
    disabled_reason: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WebhookEndpoint":
        return cls(
            id=d.get("id", ""),
            url=d.get("url", ""),
            events=d.get("events", []),
            active=d.get("active", True),
            consecutive_failures=d.get("consecutive_failures", 0),
            total_delivered=d.get("total_delivered", 0),
            total_failed=d.get("total_failed", 0),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            secret=d.get("secret", ""),
            last_success_at=d.get("last_success_at"),
            last_failure_at=d.get("last_failure_at"),
            disabled_at=d.get("disabled_at"),
            disabled_reason=d.get("disabled_reason"),
            raw=d,
        )


@dataclass
class WebhookDelivery:
    """One entry in a webhook endpoint's delivery history."""

    id: str
    webhook_id: str
    event_type: str
    status: str
    attempt_count: int
    created_at: str
    updated_at: str
    event_id: Optional[str] = None
    next_retry_at: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: Optional[str] = None
    failed_at: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WebhookDelivery":
        return cls(
            id=d.get("id", ""),
            webhook_id=d.get("webhook_id", ""),
            event_type=d.get("event_type", ""),
            status=d.get("status", ""),
            attempt_count=d.get("attempt_count", 0),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            event_id=d.get("event_id"),
            next_retry_at=d.get("next_retry_at"),
            response_status=d.get("response_status"),
            response_body=d.get("response_body"),
            delivered_at=d.get("delivered_at"),
            failed_at=d.get("failed_at"),
            error_message=d.get("error_message"),
            raw=d,
        )


@dataclass
class Event:
    """One entry in the queryable event stream."""

    seq: int
    id: str
    event_type: str
    data: Any
    created_at: str
    organization_id: Optional[str] = None
    service_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        return cls(
            seq=d.get("seq", 0),
            id=d.get("id", ""),
            event_type=d.get("event_type", ""),
            data=d.get("data"),
            created_at=d.get("created_at", ""),
            organization_id=d.get("organization_id"),
            service_id=d.get("service_id"),
            raw=d,
        )


@dataclass
class EventPage:
    """One page of the event feed."""

    events: List[Event]
    next_cursor: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EventPage":
        return cls(
            events=[Event.from_dict(e) for e in d.get("events", [])],
            next_cursor=d.get("next_cursor"),
            raw=d,
        )


# ---- Data pipeline models ----

@dataclass
class DataPipelineConfig:
    """Optional configuration for a data pipeline."""

    database_name: str = ""
    tables: List[str] = field(default_factory=list)
    topic_prefix: str = ""
    snapshot_mode: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DataPipelineConfig":
        return cls(
            database_name=d.get("database_name", ""),
            tables=d.get("tables", []),
            topic_prefix=d.get("topic_prefix", ""),
            snapshot_mode=d.get("snapshot_mode", ""),
            raw=d,
        )

    def to_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if self.database_name:
            body["database_name"] = self.database_name
        if self.tables:
            body["tables"] = self.tables
        if self.topic_prefix:
            body["topic_prefix"] = self.topic_prefix
        if self.snapshot_mode:
            body["snapshot_mode"] = self.snapshot_mode
        return body


@dataclass
class DataPipeline:
    """A data flow between two managed services."""

    id: str
    organization_id: str
    name: str
    pipeline_type: str
    source_service_id: str
    sink_service_id: str
    status: str
    config: DataPipelineConfig
    created_at: str
    updated_at: str
    provision_step: Optional[str] = None
    connector_name: Optional[str] = None
    publication_name: Optional[str] = None
    slot_name: Optional[str] = None
    topic_prefix: Optional[str] = None
    last_connector_state: Optional[str] = None
    source_lag_bytes: Optional[int] = None
    last_health_check_at: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DataPipeline":
        cfg_raw = d.get("config", {})
        return cls(
            id=d.get("id", ""),
            organization_id=d.get("organization_id", ""),
            name=d.get("name", ""),
            pipeline_type=d.get("pipeline_type", ""),
            source_service_id=d.get("source_service_id", ""),
            sink_service_id=d.get("sink_service_id", ""),
            status=d.get("status", ""),
            config=DataPipelineConfig.from_dict(cfg_raw) if cfg_raw else DataPipelineConfig(),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            provision_step=d.get("provision_step"),
            connector_name=d.get("connector_name"),
            publication_name=d.get("publication_name"),
            slot_name=d.get("slot_name"),
            topic_prefix=d.get("topic_prefix"),
            last_connector_state=d.get("last_connector_state"),
            source_lag_bytes=d.get("source_lag_bytes"),
            last_health_check_at=d.get("last_health_check_at"),
            error_message=d.get("error_message"),
            raw=d,
        )


@dataclass
class DataPipelineStatus:
    """Latest reconciler-observed status of a data pipeline."""

    id: str
    status: str
    connector_name: Optional[str] = None
    connector_state: Optional[str] = None
    task_states: Optional[Any] = None
    source_lag_bytes: Optional[int] = None
    topic_prefix: Optional[str] = None
    last_health_check_at: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DataPipelineStatus":
        return cls(
            id=d.get("id", ""),
            status=d.get("status", ""),
            connector_name=d.get("connector_name"),
            connector_state=d.get("connector_state"),
            task_states=d.get("task_states"),
            source_lag_bytes=d.get("source_lag_bytes"),
            topic_prefix=d.get("topic_prefix"),
            last_health_check_at=d.get("last_health_check_at"),
            error_message=d.get("error_message"),
            raw=d,
        )


# ---- Embedding pipeline models ----

# Embedding pipeline mode: how the pipeline processes its source table.
EmbeddingPipelineMode = Literal["continuous", "scheduled", "manual"]


@dataclass
class EmbeddingPipeline:
    """One auto-vectorization pipeline on a managed service."""

    id: str
    service_id: str
    database_name: str
    source_schema: str
    source_table: str
    text_columns: List[str]
    model_provider: str
    embedding_model: str
    model_dimensions: int
    target_schema: str
    target_table: str
    batch_size: int
    poll_interval_seconds: int
    mode: str
    status: str
    rows_processed: int
    rows_pending: int
    tokens_used: int
    created_at: str
    updated_at: str
    provider_base_url: Optional[str] = None
    schedule_cron: Optional[str] = None
    source_filter: Optional[str] = None
    max_row_retries: int = 0
    next_run_at: Optional[str] = None
    error_message: Optional[str] = None
    last_processed_at: Optional[str] = None
    last_error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbeddingPipeline":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            database_name=d.get("database_name", ""),
            source_schema=d.get("source_schema", ""),
            source_table=d.get("source_table", ""),
            text_columns=d.get("text_columns", []),
            model_provider=d.get("model_provider", ""),
            embedding_model=d.get("embedding_model", ""),
            model_dimensions=d.get("model_dimensions", 0),
            target_schema=d.get("target_schema", ""),
            target_table=d.get("target_table", ""),
            batch_size=d.get("batch_size", 100),
            poll_interval_seconds=d.get("poll_interval_seconds", 60),
            mode=d.get("mode", "continuous"),
            status=d.get("status", ""),
            rows_processed=d.get("rows_processed", 0),
            rows_pending=d.get("rows_pending", 0),
            tokens_used=d.get("tokens_used", 0),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            provider_base_url=d.get("provider_base_url"),
            schedule_cron=d.get("schedule_cron"),
            source_filter=d.get("source_filter"),
            max_row_retries=d.get("max_row_retries", 0),
            next_run_at=d.get("next_run_at"),
            error_message=d.get("error_message"),
            last_processed_at=d.get("last_processed_at"),
            last_error=d.get("last_error"),
            raw=d,
        )


@dataclass
class EmbeddingRunErrorSample:
    """One failed source row in an embedding pipeline run."""

    source_row_id: str
    error: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbeddingRunErrorSample":
        return cls(
            source_row_id=d.get("source_row_id", ""),
            error=d.get("error", ""),
            raw=d,
        )


@dataclass
class EmbeddingPipelineRun:
    """One discrete embedding job execution for a scheduled or manual
    pipeline."""

    id: str
    pipeline_id: str
    status: str
    trigger: str
    rows_scanned: int
    rows_embedded: int
    rows_failed: int
    tokens_used: int
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_message: Optional[str] = None
    error_sample: List[EmbeddingRunErrorSample] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbeddingPipelineRun":
        return cls(
            id=d.get("id", ""),
            pipeline_id=d.get("pipeline_id", ""),
            status=d.get("status", ""),
            trigger=d.get("trigger", ""),
            rows_scanned=d.get("rows_scanned", 0),
            rows_embedded=d.get("rows_embedded", 0),
            rows_failed=d.get("rows_failed", 0),
            tokens_used=d.get("tokens_used", 0),
            created_at=d.get("created_at", ""),
            started_at=d.get("started_at"),
            finished_at=d.get("finished_at"),
            error_message=d.get("error_message"),
            error_sample=[EmbeddingRunErrorSample.from_dict(e) for e in d.get("error_sample", [])],
            raw=d,
        )


# ---- Vector search models ----

# Distance operator for vector similarity search.
VectorSearchMetric = Literal["cosine", "l2", "ip"]


@dataclass
class VectorSearchFilter:
    """One column filter applied to a vector search. Only ``eq`` is
    supported."""

    column: str
    op: str
    value: Any

    def to_dict(self) -> Dict[str, Any]:
        return {"column": self.column, "op": self.op, "value": self.value}


@dataclass
class VectorSearchColumn:
    """Describes one result column."""

    name: str
    type: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VectorSearchColumn":
        return cls(name=d.get("name", ""), type=d.get("type", ""), raw=d)


@dataclass
class VectorSearchResponse:
    """Result of a vector search, with the search parameters echoed back."""

    columns: List[VectorSearchColumn]
    rows: List[List[Any]]
    row_count: int
    truncated: bool
    execution_ms: int
    metric: str
    top_k: int
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VectorSearchResponse":
        return cls(
            columns=[VectorSearchColumn.from_dict(c) for c in d.get("columns", [])],
            rows=d.get("rows", []),
            row_count=d.get("row_count", 0),
            truncated=d.get("truncated", False),
            execution_ms=d.get("execution_ms", 0),
            metric=d.get("metric", "cosine"),
            top_k=d.get("top_k", 0),
            raw=d,
        )


# ---- AI actions models ----

@dataclass
class AIActionRef:
    """How a client can act on a feed item."""

    type: str
    tier: str
    target: str
    href: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AIActionRef":
        return cls(
            type=d.get("type", ""),
            tier=d.get("tier", ""),
            target=d.get("target", ""),
            href=d.get("href", ""),
            raw=d,
        )


@dataclass
class AIActionItem:
    """One prioritized entry in the AI actions feed."""

    id: str
    kind: str
    severity: str
    service_id: str
    service_name: str
    title: str
    summary: str
    action: AIActionRef
    created_at: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AIActionItem":
        return cls(
            id=d.get("id", ""),
            kind=d.get("kind", ""),
            severity=d.get("severity", ""),
            service_id=d.get("service_id", ""),
            service_name=d.get("service_name", ""),
            title=d.get("title", ""),
            summary=d.get("summary", ""),
            action=AIActionRef.from_dict(d.get("action", {})),
            created_at=d.get("created_at", ""),
            raw=d,
        )


@dataclass
class AIActionsResponse:
    """Feed envelope for the AI actions feed."""

    items: List[AIActionItem]
    total: int
    truncated: bool
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AIActionsResponse":
        return cls(
            items=[AIActionItem.from_dict(i) for i in d.get("items", [])],
            total=d.get("total", 0),
            truncated=d.get("truncated", False),
            raw=d,
        )


@dataclass
class CopilotStep:
    """One proposed tool call in a copilot plan."""

    tool: str
    tier: str
    preview: str
    args: Optional[Dict[str, Any]] = None
    rationale: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CopilotStep":
        return cls(
            tool=d.get("tool", ""),
            tier=d.get("tier", ""),
            preview=d.get("preview", ""),
            args=d.get("args"),
            rationale=d.get("rationale", ""),
            raw=d,
        )


@dataclass
class CopilotPlan:
    """A previewable plan for a natural-language intent. Executes nothing."""

    summary: str
    steps: List[CopilotStep]
    unsupported: bool
    note: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CopilotPlan":
        return cls(
            summary=d.get("summary", ""),
            steps=[CopilotStep.from_dict(s) for s in d.get("steps", [])],
            unsupported=d.get("unsupported", False),
            note=d.get("note", ""),
            raw=d,
        )


@dataclass
class ExecuteAIActionResult:
    """Response envelope for an AI action execution attempt."""

    action_type: str
    status: str
    http_status: int
    message: str
    detail: Optional[Any] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecuteAIActionResult":
        return cls(
            action_type=d.get("action_type", ""),
            status=d.get("status", ""),
            http_status=d.get("http_status", 0),
            message=d.get("message", ""),
            detail=d.get("detail"),
            raw=d,
        )


@dataclass
class AIActionExecution:
    """API view of one persisted Action Center execution."""

    id: str
    service_id: str
    action_type: str
    status: str
    http_status: int
    created_at: str
    organization_id: Optional[str] = None
    target_id: str = ""
    actor_user_id: str = ""
    reverted_at: str = ""
    revert_status: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AIActionExecution":
        return cls(
            id=d.get("id", ""),
            service_id=d.get("service_id", ""),
            action_type=d.get("action_type", ""),
            status=d.get("status", ""),
            http_status=d.get("http_status", 0),
            created_at=d.get("created_at", ""),
            organization_id=d.get("organization_id"),
            target_id=d.get("target_id", ""),
            actor_user_id=d.get("actor_user_id", ""),
            reverted_at=d.get("reverted_at", ""),
            revert_status=d.get("revert_status", ""),
            raw=d,
        )


@dataclass
class AIActionExecutionListResponse:
    """Outcome-loop execution history envelope."""

    executions: List[AIActionExecution]
    total_count: int
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AIActionExecutionListResponse":
        return cls(
            executions=[AIActionExecution.from_dict(e) for e in d.get("executions", [])],
            total_count=d.get("total_count", 0),
            raw=d,
        )


@dataclass
class AIActionRollbackResult:
    """Response envelope for an accepted rollback."""

    execution_id: str
    action_type: str
    revert_status: str
    message: str
    task_id: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AIActionRollbackResult":
        return cls(
            execution_id=d.get("execution_id", ""),
            action_type=d.get("action_type", ""),
            revert_status=d.get("revert_status", ""),
            message=d.get("message", ""),
            task_id=d.get("task_id", ""),
            raw=d,
        )


# ---- Compliance models ----

@dataclass
class ControlAssertion:
    """One evaluated control in a compliance packet."""

    control_id: str
    title: str
    assertion: str
    status: str
    evidence_refs: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ControlAssertion":
        return cls(
            control_id=d.get("control_id", ""),
            title=d.get("title", ""),
            assertion=d.get("assertion", ""),
            status=d.get("status", ""),
            evidence_refs=d.get("evidence_refs", []),
            raw=d,
        )


@dataclass
class CompliancePacket:
    """Structured evidence packet covering one compliance framework and period."""

    schema_version: str
    framework: str
    generated_at: str
    period_start: str
    period_end: str
    organization: Dict[str, Any]
    scope_boundary: str
    controls: List[ControlAssertion]
    summary: Dict[str, Any]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CompliancePacket":
        return cls(
            schema_version=d.get("schema_version", ""),
            framework=d.get("framework", ""),
            generated_at=d.get("generated_at", ""),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
            organization=d.get("organization", {}),
            scope_boundary=d.get("scope_boundary", ""),
            controls=[ControlAssertion.from_dict(c) for c in d.get("controls", [])],
            summary=d.get("summary", {}),
            raw=d,
        )


@dataclass
class CompliancePacketSignature:
    """Detached signature covering the canonical serialization of a compliance packet."""

    algorithm: str
    key_id: str
    value: str
    canonical_sha256: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CompliancePacketSignature":
        return cls(
            algorithm=d.get("algorithm", ""),
            key_id=d.get("key_id", ""),
            value=d.get("value", ""),
            canonical_sha256=d.get("canonical_sha256", ""),
            raw=d,
        )


@dataclass
class CompliancePacketResponse:
    """GET /compliance-reports/{id} response: packet with its detached signature."""

    packet: CompliancePacket
    signature: CompliancePacketSignature
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CompliancePacketResponse":
        return cls(
            packet=CompliancePacket.from_dict(d.get("packet", {})),
            signature=CompliancePacketSignature.from_dict(d.get("signature", {})),
            raw=d,
        )


@dataclass
class GenerateComplianceReportResponse:
    """Response from POST /compliance-reports: the new report ID plus the packet."""

    report_id: str
    packet: CompliancePacket
    signature: CompliancePacketSignature
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GenerateComplianceReportResponse":
        return cls(
            report_id=d.get("report_id", ""),
            packet=CompliancePacket.from_dict(d.get("packet", {})),
            signature=CompliancePacketSignature.from_dict(d.get("signature", {})),
            raw=d,
        )


@dataclass
class ComplianceReportRecord:
    """One entry in the compliance report index for an organization."""

    id: str
    organization_id: str
    framework: str
    schema_version: str
    period_start: str
    period_end: str
    generated_at: str
    generated_by: str
    signing_key_id: str
    algorithm: str
    status: str
    has_pdf: bool
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ComplianceReportRecord":
        return cls(
            id=d.get("id", ""),
            organization_id=d.get("organization_id", ""),
            framework=d.get("framework", ""),
            schema_version=d.get("schema_version", ""),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
            generated_at=d.get("generated_at", ""),
            generated_by=d.get("generated_by", ""),
            signing_key_id=d.get("signing_key_id", ""),
            algorithm=d.get("algorithm", ""),
            status=d.get("status", ""),
            has_pdf=d.get("has_pdf", False),
            raw=d,
        )


@dataclass
class ComplianceSigningKey:
    """One public signing key in the platform key set."""

    key_id: str
    algorithm: str
    public_key: str
    active: bool
    retired_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ComplianceSigningKey":
        return cls(
            key_id=d.get("key_id", ""),
            algorithm=d.get("algorithm", ""),
            public_key=d.get("public_key", ""),
            active=d.get("active", False),
            retired_at=d.get("retired_at"),
            raw=d,
        )


@dataclass
class ComplianceSigningKeySet:
    """JWKS-style response from /.well-known/compliance-signing-keys."""

    algorithm: str
    keys: List[ComplianceSigningKey]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ComplianceSigningKeySet":
        return cls(
            algorithm=d.get("algorithm", ""),
            keys=[ComplianceSigningKey.from_dict(k) for k in d.get("keys", [])],
            raw=d,
        )


# ---- Companion-app attachment models ----

@dataclass
class AttachmentCatalogEntry:
    """One entry in the companion-app attachment catalog.

    ``kind`` is the stable identifier used when creating an attachment
    (e.g. ``"metabase"``). ``requires_parent_kinds`` lists the database
    engine types the companion app can attach to.
    """

    kind: str
    display_name: str
    description: str
    category: str
    default_plan: str
    requires_parent_kinds: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AttachmentCatalogEntry":
        return cls(
            kind=d.get("kind", ""),
            display_name=d.get("display_name", ""),
            description=d.get("description", ""),
            category=d.get("category", ""),
            default_plan=d.get("default_plan", ""),
            requires_parent_kinds=d.get("requires_parent_kinds", []),
            raw=d,
        )


@dataclass
class AttachmentSummary:
    """Summary of one companion-app attachment on a managed service."""

    attachment_id: str
    app_service_id: str
    kind: str
    name: str
    status: str
    wiring_status: str
    url: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AttachmentSummary":
        return cls(
            attachment_id=d.get("attachment_id", ""),
            app_service_id=d.get("app_service_id", ""),
            kind=d.get("kind", ""),
            name=d.get("name", ""),
            status=d.get("status", ""),
            wiring_status=d.get("wiring_status", ""),
            url=d.get("url", ""),
            raw=d,
        )


@dataclass
class AttachmentCredentials:
    """Admin credentials for a companion-app attachment.

    ``generated`` holds any extra key/value pairs the companion app
    exposes (e.g. API tokens, embed secrets).
    """

    admin_email: str
    admin_password: str
    login_url: str
    generated: Dict[str, str] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AttachmentCredentials":
        return cls(
            admin_email=d.get("admin_email", ""),
            admin_password=d.get("admin_password", ""),
            login_url=d.get("login_url", ""),
            generated=d.get("generated", {}),
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
