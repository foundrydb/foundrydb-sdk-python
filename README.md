# foundrydb

Official Python SDK for the [FoundryDB](https://foundrydb.com) managed database platform.

## Installation

```bash
pip install foundrydb
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
| `opensearch` | 2.19 |
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
    version="2.19",
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

## License

MIT
