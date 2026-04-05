"""
FoundryDB Python SDK
====================

Official Python client for the FoundryDB managed database platform.

Sync usage::

    from foundrydb import FoundryDB

    client = FoundryDB(
        api_url="https://api.foundrydb.com",
        username="admin",
        password="admin",
    )
    services = client.services.list()

Async usage::

    import asyncio
    from foundrydb import AsyncFoundryDB

    async def main():
        async with AsyncFoundryDB(
            api_url="https://api.foundrydb.com",
            username="admin",
            password="admin",
        ) as client:
            services = await client.services.list()

    asyncio.run(main())
"""

from .client import FoundryDB, AsyncFoundryDB
from .types import (
    DatabaseType,
    CreateServiceRequest,
    FoundryDBError,
    Organization,
    Service,
    ServicePreset,
    DNSRecord,
    DatabaseUser,
    RevealPasswordResponse,
    Backup,
    TriggerBackupResponse,
    ServiceMetrics,
    LogsTaskResponse,
    LogsResultResponse,
)
from .services import ServicesAPI, AsyncServicesAPI
from .users import UsersAPI, AsyncUsersAPI
from .backups import BackupsAPI, AsyncBackupsAPI
from .monitoring import MonitoringAPI, AsyncMonitoringAPI
from .organizations import OrganizationsAPI, AsyncOrganizationsAPI

__version__ = "0.2.0"
__all__ = [
    "FoundryDB",
    "AsyncFoundryDB",
    "DatabaseType",
    "CreateServiceRequest",
    "FoundryDBError",
    "Organization",
    "Service",
    "ServicePreset",
    "DNSRecord",
    "DatabaseUser",
    "RevealPasswordResponse",
    "Backup",
    "TriggerBackupResponse",
    "ServiceMetrics",
    "LogsTaskResponse",
    "LogsResultResponse",
    "ServicesAPI",
    "AsyncServicesAPI",
    "UsersAPI",
    "AsyncUsersAPI",
    "BackupsAPI",
    "AsyncBackupsAPI",
    "MonitoringAPI",
    "AsyncMonitoringAPI",
    "OrganizationsAPI",
    "AsyncOrganizationsAPI",
]
