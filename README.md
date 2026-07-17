# foundrydb

Official Python SDK for the [FoundryDB](https://foundrydb.com) managed database platform.

## Installation

```bash
pip install foundrydb-sdk
```

The distribution is published as `foundrydb-sdk`; the import package is `foundrydb`:

```python
import foundrydb
```

## Requirements

- Python 3.9+
- [`httpx`](https://www.python-httpx.org/) (automatically installed)

## Quick Start

```python
from foundrydb import FoundryDB

client = FoundryDB(
    api_url="https://api.foundrydb.com",
    username="admin",
    password="admin",
)

services = client.services.list()
for svc in services:
    print(svc.id, svc.name, svc.status)
```

## Organizations

FoundryDB supports personal and team organizations. You can list all organizations
your account belongs to, and scope a client (or individual service creation requests)
to a specific organization.

### List organizations

```python
orgs = client.organizations.list()
for org in orgs:
    print(org.id, org.name, org.slug, "personal=" + str(org.is_personal))
```

Each entry is an `Organization` dataclass with fields: `id`, `name`, `slug`, `is_personal`.

### Scope client to an organization

Pass `organization_id` when constructing the client. Every request will then include
the `X-Active-Org-ID` header automatically.

```python
client = FoundryDB(
    api_url="https://api.foundrydb.com",
    username="admin",
    password="admin",
    organization_id="org_abc123",
)
```

### Override organization per request

You can also pass `organization_id` directly to `services.create()` to override the
client-level setting for a single call:

```python
service = client.services.create(
    name="team-pg",
    database_type="postgresql",
    version="17",
    plan_name="tier-2",
    zone="se-sto1",
    storage_size_gb=50,
    storage_tier="maxiops",
    organization_id="org_team456",
)
```

## Supported Database Types

| Type | Versions |
|------|----------|
| `postgresql` | 14, 15, 16, 17, 18 |
| `mysql` | 8.4 |
| `mongodb` | 6.0, 7.0, 8.0 |
| `valkey` | 7.2, 8.0, 8.1, 9.0 |
| `kafka` | 3.6, 3.7, 3.8, 3.9, 4.0 |
| `opensearch: 2 |
| `mssql` | 4.8 |

## Usage

### Services

```python
# List all managed services
services = client.services.list()

# Create a single-node PostgreSQL 17 service
service = client.services.create(
    name="my-pg",
    database_type="postgresql",
    version="17",
    plan_name="tier-2",
    zone="se-sto1",
    storage_size_gb=50,
    storage_tier="maxiops",
)
print("Created:", service.id, service.status)

# Create a 3-node HA PostgreSQL cluster with auto-failover
ha_service = client.services.create(
    name="my-pg-ha",
    database_type="postgresql",
    version="17",
    plan_name="tier-2",
    zone="se-sto1",
    storage_size_gb=100,
    storage_tier="maxiops",
    node_count=3,
    auto_failover_enabled=True,
    replication_mode="async",
    encryption_enabled=True,
    allowed_cidrs=["203.0.113.0/24"],
)

# Create an OpenSearch service
search_svc = client.services.create(
    name="my-search",
    database_type="opensearch",
    version="2",
    plan_name="tier-2",
    zone="se-sto1",
    storage_size_gb=50,
    storage_tier="maxiops",
)

# Create a Kafka cluster
kafka_svc = client.services.create(
    name="my-kafka",
    database_type="kafka",
    version="4.0",
    plan_name="tier-2",
    zone="se-sto1",
    storage_size_gb=100,
    storage_tier="maxiops",
    node_count=3,
)

# Get a service by ID
svc = client.services.get(service.id)

# Update a service (e.g. change allowed CIDRs)
client.services.update(service.id, allowed_cidrs=["203.0.113.0/24"])

# Delete a service
client.services.delete(service.id)
```

#### `create()` parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | yes | Display name |
| `database_type` | DatabaseType | yes | Engine (see table above) |
| `version` | str | yes | Engine version string |
| `plan_name` | str | yes | Compute plan (e.g. `"tier-2"`) |
| `zone` | str | yes | Deployment zone (e.g. `"se-sto1"`) |
| `storage_size_gb` | int | yes | Data disk size in GB |
| `storage_tier` | str | yes | `"standard"` or `"maxiops"` |
| `organization_id` | str | no | Override active org for this request |
| `node_count` | int | no | Number of nodes (default 1) |
| `auto_failover_enabled` | bool | no | Enable automatic failover |
| `replication_mode` | str | no | `"async"` or `"sync"` |
| `encryption_enabled` | bool | no | At-rest encryption |
| `allowed_cidrs` | list[str] | no | Allowed source CIDRs |
| `maintenance_window` | str | no | Preferred maintenance window |

### Database Users and Credentials

```python
# List users
users = client.users.list(service_id)
for user in users:
    print(user.username)

# Reveal password and connection string
creds = client.users.reveal_password(service_id, "admin")
print(creds.connection_string)
# postgresql://admin:s3cret@my-pg.foundrydb.com:5432/defaultdb?sslmode=require
```

### Backups

```python
# List backups
backups = client.backups.list(service_id)
for b in backups:
    print(b.id, b.status, b.backup_type)

# Trigger an on-demand backup
result = client.backups.trigger(service_id)
```

### Monitoring

```python
# Get current metrics
metrics = client.monitoring.get_metrics(service_id)
print(f"CPU: {metrics.cpu_usage_percent}%")
print(f"Memory: {metrics.memory_usage_percent}%")

# Request logs and poll manually
task = client.monitoring.request_logs(service_id, lines=200)
result = client.monitoring.get_logs(service_id, task.task_id)
print(result.logs)

# Or use the convenience wrapper (auto-polls until done)
logs = client.monitoring.fetch_logs(service_id, lines=500)
print(logs)
```

### Edge Gateway

The edge gateway sits in front of app services and provides custom domains with automated TLS, path-based caching, a token-bucket rate limiter, and a WAF. All methods are on `client.edge`:

```python
from foundrydb import EdgeCacheRule, EdgeRateLimit

# Add a custom domain (starts in pending_verification; platform verifies CNAME and issues TLS)
domain = client.edge.create_domain(app.id, "shop.acme.com")
print(domain.cname_target)   # "edge.foundrydb.com" -- point your CNAME here

# Trigger an immediate verification pass instead of waiting for the background worker
domain = client.edge.verify_domain(app.id, domain.id)

# List all domains attached to the app
domains = client.edge.list_domains(app.id)
for d in domains:
    print(d.domain, d.status)

# Remove a domain (idempotent: 404 is treated as success)
client.edge.delete_domain(app.id, domain.id)

# Inspect the edge overview: enabled flag, home PoP, CNAME target, per-PoP convergence
status = client.edge.get_status(app.id)
print(status.edge_enabled, status.home_pop, status.config_version)
for pop in status.applications:
    print(pop.zone, pop.status, pop.applied_version)

# Update customer-tunable edge settings (cache rules, rate limit, WAF mode)
settings = client.edge.update_settings(
    app.id,
    cache_rules=[EdgeCacheRule(path_prefix="/static/", ttl_seconds=86400)],
    rate_limit=EdgeRateLimit(requests_per_second=100, burst=200, key="ip"),
    waf_mode="detect",
)
print(settings.config_version)   # version the fleet will converge on
```

#### `update_settings()` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cache_rules` | `list[EdgeCacheRule]` or `None` | Path-prefix cache rules. Pass `[]` to clear. |
| `rate_limit` | `EdgeRateLimit` or `None` | Token-bucket rate limit. |
| `waf_mode` | `str` or `None` | `"off"` or `"detect"`. |

#### Edge models

| Model | Fields |
|-------|--------|
| `EdgeDomain` | `id`, `service_id`, `user_id`, `domain`, `status`, `cname_target`, `certificate_id`, `verification_checked_at`, `error_message`, `created_at`, `updated_at` |
| `EdgeStatus` | `edge_enabled`, `home_pop`, `cname_target`, `config_version`, `applications` |
| `EdgeAppApplication` | `zone`, `applied_version`, `status`, `error_message` |
| `EdgeSettings` | `waf_mode`, `config_version`, `cache_rules`, `rate_limit` |
| `EdgeCacheRule` | `path_prefix`, `ttl_seconds` |
| `EdgeRateLimit` | `requests_per_second`, `burst`, `key` |

`EdgeDomainStatus` values: `pending_verification`, `verifying`, `issuing_certificate`, `propagating`, `active`, `failed`, `deleting`.

### Managed Inference Adapters

Manage the customer LoRA fine-tuned adapter registry for a managed inference service (an open-weight LLM served by vLLM on a dedicated GPU). Register an uploaded adapter version, then promote it to hot-load it into vLLM with no restart. Methods live on `client.inference_services`.

```python
# 1. After uploading the adapter artifact (adapter_model.safetensors +
#    adapter_config.json) to the org's Files bucket, register the version.
adapter = client.inference_services.register_adapter(
    base_model_id="mistral-small",
    served_model_name="support-bot",
    version=3,
    files_bucket="org-1-adapters",
    files_key_prefix="support-bot/v3",
    adapter_sha256="3b1e...",  # 64-char lowercase hex sha256
    size_bytes=104857600,
    base_model_license="apache-2.0",
)
print(adapter.status)  # "uploaded" — not yet on a GPU

# 2. List the versions relevant to a service: the ones bound to it (active +
#    superseded history) plus the org's uploaded, not-yet-promoted versions
#    trained on the service's base model.
for a in client.inference_services.list_adapters(service_id):
    print(a.served_model_name, a.version, a.status)

# 3. Promote a version onto the serving GPU. It becomes "active" and any
#    previously active version is marked "superseded".
active = client.inference_services.promote_adapter(service_id, adapter.id)
print(active.status, active.promoted_at)  # "active", <timestamp>

# Rollback is the same call on a prior (superseded) version — no separate route.
client.inference_services.promote_adapter(service_id, previous_adapter_id)
```

Once active, the service answers to the adapter as `foundrydb_managed/<served_model_name>` on its OpenAI-compatible endpoint.

## Async Client

All methods have async equivalents. Use `AsyncFoundryDB` as an async context manager:

```python
import asyncio
from foundrydb import AsyncFoundryDB

async def main():
    async with AsyncFoundryDB(
        api_url="https://api.foundrydb.com",
        username="admin",
        password="admin",
        organization_id="org_abc123",   # optional org scoping
    ) as client:
        # List organizations
        orgs = await client.organizations.list()

        # Create a service
        service = await client.services.create(
            name="async-pg",
            database_type="postgresql",
            version="17",
            plan_name="tier-2",
            zone="se-sto1",
            storage_size_gb=50,
            storage_tier="maxiops",
        )

        creds = await client.users.reveal_password(service.id, "admin")
        print(creds.connection_string)

        logs = await client.monitoring.fetch_logs(service.id)
        print(logs)

asyncio.run(main())
```

## Error Handling

API errors raise `FoundryDBError` with `status_code` and `body` attributes:

```python
from foundrydb import FoundryDB, FoundryDBError

try:
    client.services.get("non-existent-id")
except FoundryDBError as e:
    print(f"API error {e.status_code}: {e}")
    print(e.body)  # raw dict from the API
```

## Configuration

```python
client = FoundryDB(
    api_url="https://api.foundrydb.com",  # required
    username="admin",                      # required
    password="admin",                      # required
    timeout=30.0,                          # optional, default 30s
    organization_id="org_abc123",          # optional, scopes all requests
)
```

## Typed Models

All responses are typed dataclasses:

```python
from foundrydb import (
    Organization,
    Service,
    DatabaseUser,
    Backup,
    ServiceMetrics,
    CreateServiceRequest,
)
```

Each model also exposes `.raw` for direct access to the full JSON response dict.

### `Organization`

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique organization ID |
| `name` | str | Display name |
| `slug` | str | URL-safe identifier |
| `is_personal` | bool | True for a user's personal org |

### `CreateServiceRequest`

A dataclass that mirrors the `create()` keyword arguments. You can construct it
directly and call `.to_dict()` to get the request payload:

```python
from foundrydb import CreateServiceRequest

req = CreateServiceRequest(
    name="my-valkey",
    database_type="valkey",
    version="8.1",
    plan_name="tier-2",
    zone="se-sto1",
    storage_size_gb=20,
    storage_tier="maxiops",
    node_count=3,
    auto_failover_enabled=True,
)
print(req.to_dict())
```

## Compliance Evidence Packets

FoundryDB generates signed compliance evidence packets for SOC 2 Type II and
GDPR Article 30 Records of Processing Activities (ROPA). Packets are persisted
per organization and can be retrieved as structured JSON or as rendered PDFs.

### Generate a report

```python
result = client.compliance.generate_compliance_report(
    org_id="org_abc123",
    framework="soc2",          # or "gdpr_ropa"
)
print(result.report_id)
print(result.packet.framework, result.packet.period_start, result.packet.period_end)
print(result.signature.key_id, result.signature.algorithm)
```

### List existing reports

```python
reports = client.compliance.list_compliance_reports(org_id="org_abc123")
for r in reports:
    print(r.id, r.framework, r.generated_at, r.status, r.has_pdf)
```

### Download a report as JSON

```python
resp = client.compliance.download_compliance_report_json(
    org_id="org_abc123",
    report_id=reports[0].id,
)
for ctrl in resp.packet.controls:
    print(ctrl.control_id, ctrl.status, ctrl.title)
```

### Download a report as PDF

```python
pdf_bytes = client.compliance.download_compliance_report_pdf(
    org_id="org_abc123",
    report_id=reports[0].id,
)
with open("compliance_report.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Verify signatures offline (no credentials required)

```python
key_set = client.compliance.compliance_signing_keys()
for key in key_set.keys:
    print(key.key_id, key.algorithm, "active=" + str(key.active))
```

The `/.well-known/compliance-signing-keys` endpoint is public and does not
require authentication, allowing offline verification of evidence packets.

### List compliance subscriptions

```python
subs = client.compliance.list_compliance_subscriptions(org_id="org_abc123")
for s in subs:
    print(s.framework, s.enabled, s.monthly_price_eur, s.subscribed_at, s.canceled_at)
```

Each entry is a `ComplianceSubscription` with fields: `framework`, `enabled`,
`monthly_price_eur`, `subscribed_at`, `canceled_at`.

### Subscribe to a compliance framework

```python
sub = client.compliance.subscribe_compliance_framework(
    org_id="org_abc123",
    framework="soc2",   # or "gdpr_ropa", "dora", "eu_ai_act"
)
print(sub.framework, sub.enabled, sub.subscribed_at)
```

### Unsubscribe from a compliance framework

```python
client.compliance.unsubscribe_compliance_framework(
    org_id="org_abc123",
    framework="soc2",
)
```

### Rotate the compliance signing key (admin only)

```python
key_set = client.compliance.rotate_compliance_signing_key()
for key in key_set.keys:
    print(key.key_id, "active=" + str(key.active), key.retired_at)
```

Generates a fresh Ed25519 keypair, promotes it to active, and retires the
previous key. Previously signed packets remain verifiable using the retired key.

## License

MIT
