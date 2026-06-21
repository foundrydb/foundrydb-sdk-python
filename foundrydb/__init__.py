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
    AppContainerConfig,
    AppDeployStep,
    AppDeployment,
    AppService,
    ServiceAttachment,
    SmtpConfig,
    AuthTheme,
    IdpProviderRequest,
    IdpProviderConfig,
    AuthEnableRequest,
    AuthConfiguration,
    AuthSigningKey,
    AuthConfigurationWithKeys,
    EdgeDomain,
    EdgeDomainStatus,
    EdgeCacheRule,
    EdgeRateLimit,
    EdgeRateLimitKey,
    EdgeWAFMode,
    EdgeAppApplication,
    EdgeStatus,
    EdgeSettings,
    # App Jobs
    AppJob,
    AppJobInvocation,
    AppJobLogLines,
    AppJobInvocationLogs,
    # Queues
    Queue,
    QueueEnqueueMessageIDs,
    QueueEnqueueResult,
    QueueStats,
    QueueStatsResult,
    # File Services
    FilesBucket,
    FilesConfig,
    FilesService,
    FilesAccessKey,
    FilesAccessKeyWithSecret,
    FilesPresignedURL,
    FilesObject,
    FilesObjectPage,
    # Inference
    InferenceProviderConfig,
    InferenceKey,
    CreateInferenceKeyResult,
    OrgInferenceSettings,
    InferenceUsageRow,
    InferenceUsageSummary,
    # Webhooks / Events
    WebhookEndpoint,
    WebhookDelivery,
    Event,
    EventPage,
    # Data Pipelines
    DataPipelineConfig,
    DataPipeline,
    DataPipelineStatus,
    # Embedding Pipelines
    EmbeddingPipelineMode,
    EmbeddingPipeline,
    EmbeddingRunErrorSample,
    EmbeddingPipelineRun,
    # Vector Search
    VectorSearchMetric,
    VectorSearchFilter,
    VectorSearchColumn,
    VectorSearchResponse,
    # AI Actions
    AIActionRef,
    AIActionItem,
    AIActionsResponse,
    CopilotStep,
    CopilotPlan,
    ExecuteAIActionResult,
    AIActionExecution,
    AIActionExecutionListResponse,
    AIActionRollbackResult,
    # Compliance
    ControlAssertion,
    CompliancePacket,
    CompliancePacketSignature,
    CompliancePacketResponse,
    GenerateComplianceReportResponse,
    ComplianceReportRecord,
    ComplianceSigningKey,
    ComplianceSigningKeySet,
    # Attachments
    AttachmentCatalogEntry,
    AttachmentSummary,
    AttachmentCredentials,
)
from .services import ServicesAPI, AsyncServicesAPI
from .users import UsersAPI, AsyncUsersAPI
from .backups import BackupsAPI, AsyncBackupsAPI
from .monitoring import MonitoringAPI, AsyncMonitoringAPI
from .organizations import OrganizationsAPI, AsyncOrganizationsAPI
from .app_services import AppServicesAPI, AsyncAppServicesAPI
from .edge import EdgeAPI, AsyncEdgeAPI
from .app_jobs import AppJobsAPI, AsyncAppJobsAPI
from .queues import QueuesAPI, AsyncQueuesAPI
from .file_services import FileServicesAPI, AsyncFileServicesAPI
from .inference import InferenceAPI, AsyncInferenceAPI
from .webhooks import WebhooksAPI, AsyncWebhooksAPI
from .data_pipelines import DataPipelinesAPI, AsyncDataPipelinesAPI
from .embedding_pipelines import EmbeddingPipelinesAPI, AsyncEmbeddingPipelinesAPI
from .vector_search import VectorSearchAPI, AsyncVectorSearchAPI
from .ai_actions import AIActionsAPI, AsyncAIActionsAPI
from .compliance import ComplianceAPI, AsyncComplianceAPI
from .attachments import AttachmentsAPI, AsyncAttachmentsAPI

__version__ = "0.5.1"
__all__ = [
    # Clients
    "FoundryDB",
    "AsyncFoundryDB",
    # Core types
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
    # App Services types
    "AppContainerConfig",
    "AppDeployStep",
    "AppDeployment",
    "AppService",
    "ServiceAttachment",
    "SmtpConfig",
    "AuthTheme",
    "IdpProviderRequest",
    "IdpProviderConfig",
    "AuthEnableRequest",
    "AuthConfiguration",
    "AuthSigningKey",
    "AuthConfigurationWithKeys",
    # Edge types
    "EdgeDomain",
    "EdgeDomainStatus",
    "EdgeCacheRule",
    "EdgeRateLimit",
    "EdgeRateLimitKey",
    "EdgeWAFMode",
    "EdgeAppApplication",
    "EdgeStatus",
    "EdgeSettings",
    # App Jobs types
    "AppJob",
    "AppJobInvocation",
    "AppJobLogLines",
    "AppJobInvocationLogs",
    # Queue types
    "Queue",
    "QueueEnqueueMessageIDs",
    "QueueEnqueueResult",
    "QueueStats",
    "QueueStatsResult",
    # File Services types
    "FilesBucket",
    "FilesConfig",
    "FilesService",
    "FilesAccessKey",
    "FilesAccessKeyWithSecret",
    "FilesPresignedURL",
    "FilesObject",
    "FilesObjectPage",
    # Inference types
    "InferenceProviderConfig",
    "InferenceKey",
    "CreateInferenceKeyResult",
    "OrgInferenceSettings",
    "InferenceUsageRow",
    "InferenceUsageSummary",
    # Webhook / Event types
    "WebhookEndpoint",
    "WebhookDelivery",
    "Event",
    "EventPage",
    # Data Pipeline types
    "DataPipelineConfig",
    "DataPipeline",
    "DataPipelineStatus",
    # Embedding Pipeline types
    "EmbeddingPipelineMode",
    "EmbeddingPipeline",
    "EmbeddingRunErrorSample",
    "EmbeddingPipelineRun",
    # Vector Search types
    "VectorSearchMetric",
    "VectorSearchFilter",
    "VectorSearchColumn",
    "VectorSearchResponse",
    # AI Actions types
    "AIActionRef",
    "AIActionItem",
    "AIActionsResponse",
    "CopilotStep",
    "CopilotPlan",
    "ExecuteAIActionResult",
    "AIActionExecution",
    "AIActionExecutionListResponse",
    "AIActionRollbackResult",
    # Compliance types
    "ControlAssertion",
    "CompliancePacket",
    "CompliancePacketSignature",
    "CompliancePacketResponse",
    "GenerateComplianceReportResponse",
    "ComplianceReportRecord",
    "ComplianceSigningKey",
    "ComplianceSigningKeySet",
    # Attachment types
    "AttachmentCatalogEntry",
    "AttachmentSummary",
    "AttachmentCredentials",
    # API classes (sync)
    "ServicesAPI",
    "UsersAPI",
    "BackupsAPI",
    "MonitoringAPI",
    "OrganizationsAPI",
    "AppServicesAPI",
    "EdgeAPI",
    "AppJobsAPI",
    "QueuesAPI",
    "FileServicesAPI",
    "InferenceAPI",
    "WebhooksAPI",
    "DataPipelinesAPI",
    "EmbeddingPipelinesAPI",
    "VectorSearchAPI",
    "AIActionsAPI",
    "ComplianceAPI",
    "AttachmentsAPI",
    # API classes (async)
    "AsyncServicesAPI",
    "AsyncUsersAPI",
    "AsyncBackupsAPI",
    "AsyncMonitoringAPI",
    "AsyncOrganizationsAPI",
    "AsyncAppServicesAPI",
    "AsyncEdgeAPI",
    "AsyncAppJobsAPI",
    "AsyncQueuesAPI",
    "AsyncFileServicesAPI",
    "AsyncInferenceAPI",
    "AsyncWebhooksAPI",
    "AsyncDataPipelinesAPI",
    "AsyncEmbeddingPipelinesAPI",
    "AsyncVectorSearchAPI",
    "AsyncAIActionsAPI",
    "AsyncComplianceAPI",
    "AsyncAttachmentsAPI",
]
