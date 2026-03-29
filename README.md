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

## Usage

### Services

```python
# List all managed services
services = client.services.list()

# Create a new PostgreSQL service
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

# Get a service by ID
svc = client.services.get(service.id)

# Update a service (e.g. change allowed CIDRs)
client.services.update(service.id, allowed_cidrs=["203.0.113.0/24"])

# Delete a service
client.services.delete(service.id)
```

Supported `database_type` values: `postgresql`, `mysql`, `mongodb`, `valkey`, `kafka`

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

```python
import asyncio
from foundrydb import AsyncFoundryDB

async def main():
    async with AsyncFoundryDB(
        api_url="https://api.foundrydb.com",
        username="admin",
        password="admin",
    ) as client:
        # All the same methods — just await them
        services = await client.services.list()

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
)
```

## Typed Models

All responses are typed dataclasses:

```python
from foundrydb import Service, DatabaseUser, Backup, ServiceMetrics
```

Each model also exposes `.raw` for direct access to the full JSON response dict.

## License

MIT
