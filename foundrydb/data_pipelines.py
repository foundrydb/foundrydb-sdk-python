"""
FoundryDB SDK - Data Pipelines API (sync and async).

Data pipelines stream data between managed services. The initial supported
topology is CDC from PostgreSQL to Kafka (cdc_pg_to_kafka) via a Debezium
connector. Provisioning is asynchronous: poll get() until the status is
Running.
"""
from __future__ import annotations

from typing import List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import DataPipeline, DataPipelineConfig, DataPipelineStatus


class DataPipelinesAPI:
    """Manages data pipelines owned by an organization (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        org_id: str,
        *,
        name: str,
        pipeline_type: str,
        source_service_id: str,
        sink_service_id: str,
        config: Optional[DataPipelineConfig] = None,
    ) -> DataPipeline:
        """Create a data pipeline between two services.

        Provisioning is asynchronous: the returned pipeline is in the Pending
        state. Poll :meth:`get` until it reaches Running.

        Args:
            org_id: Organization ID that owns both services.
            name: Pipeline name.
            pipeline_type: Pipeline topology, e.g. ``"cdc_pg_to_kafka"``.
            source_service_id: ID of the source managed service.
            sink_service_id: ID of the sink managed service.
            config: Optional pipeline configuration (tables, topic prefix,
                snapshot mode).
        """
        body = {
            "name": name,
            "pipeline_type": pipeline_type,
            "source_service_id": source_service_id,
            "sink_service_id": sink_service_id,
        }
        if config is not None:
            body["config"] = config.to_dict()  # type: ignore[assignment]
        data = self._http.post(f"/organizations/{org_id}/pipelines", body)
        return DataPipeline.from_dict(data)

    def list(self, org_id: str) -> List[DataPipeline]:
        """Return all data pipelines owned by the organization."""
        data = self._http.get(f"/organizations/{org_id}/pipelines")
        return [DataPipeline.from_dict(p) for p in data.get("pipelines", [])]

    def get(self, org_id: str, pipeline_id: str) -> Optional[DataPipeline]:
        """Return one data pipeline, or ``None`` when not found."""
        try:
            data = self._http.get(
                f"/organizations/{org_id}/pipelines/{pipeline_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return DataPipeline.from_dict(data)

    def delete(self, org_id: str, pipeline_id: str) -> None:
        """Schedule asynchronous teardown of the data pipeline."""
        self._http.delete(f"/organizations/{org_id}/pipelines/{pipeline_id}")

    def get_status(self, pipeline_id: str) -> Optional[DataPipelineStatus]:
        """Return the latest reconciler-observed status of a pipeline.

        Includes connector state, per-task states, and source lag. Returns
        ``None`` when the pipeline does not exist (404).
        """
        try:
            data = self._http.get(f"/pipelines/{pipeline_id}/status")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return DataPipelineStatus.from_dict(data)


class AsyncDataPipelinesAPI:
    """Manages data pipelines owned by an organization (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        org_id: str,
        *,
        name: str,
        pipeline_type: str,
        source_service_id: str,
        sink_service_id: str,
        config: Optional[DataPipelineConfig] = None,
    ) -> DataPipeline:
        """Create a data pipeline between two services."""
        body = {
            "name": name,
            "pipeline_type": pipeline_type,
            "source_service_id": source_service_id,
            "sink_service_id": sink_service_id,
        }
        if config is not None:
            body["config"] = config.to_dict()  # type: ignore[assignment]
        data = await self._http.post(f"/organizations/{org_id}/pipelines", body)
        return DataPipeline.from_dict(data)

    async def list(self, org_id: str) -> List[DataPipeline]:
        """Return all data pipelines owned by the organization."""
        data = await self._http.get(f"/organizations/{org_id}/pipelines")
        return [DataPipeline.from_dict(p) for p in data.get("pipelines", [])]

    async def get(self, org_id: str, pipeline_id: str) -> Optional[DataPipeline]:
        """Return one data pipeline, or ``None`` when not found."""
        try:
            data = await self._http.get(
                f"/organizations/{org_id}/pipelines/{pipeline_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return DataPipeline.from_dict(data)

    async def delete(self, org_id: str, pipeline_id: str) -> None:
        """Schedule asynchronous teardown of the data pipeline."""
        await self._http.delete(f"/organizations/{org_id}/pipelines/{pipeline_id}")

    async def get_status(self, pipeline_id: str) -> Optional[DataPipelineStatus]:
        """Return the latest reconciler-observed status of a pipeline."""
        try:
            data = await self._http.get(f"/pipelines/{pipeline_id}/status")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return DataPipelineStatus.from_dict(data)
