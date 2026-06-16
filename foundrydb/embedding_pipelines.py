"""
FoundryDB SDK - Embedding Pipelines API (sync and async).

Embedding pipelines provide managed auto-vectorization for PostgreSQL services
with pgvector. A pipeline watches a source table, embeds configured text
columns through the customer's own provider key, and writes vectors into an
indexed companion table.

Three modes are supported:
  - continuous: process rows as they change (trigger-driven)
  - scheduled:  process in discrete runs on a cron schedule
  - manual:     process in discrete runs when explicitly triggered
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    EmbeddingPipeline,
    EmbeddingPipelineRun,
)


class EmbeddingPipelinesAPI:
    """Manages embedding pipelines on PostgreSQL services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    @staticmethod
    def _base(service_id: str) -> str:
        return f"/managed-services/{service_id}/embedding-pipelines"

    # ------------------------------------------------------------------
    # Pipeline definitions
    # ------------------------------------------------------------------

    def list(self, service_id: str) -> List[EmbeddingPipeline]:
        """Return all embedding pipelines on the service."""
        data = self._http.get(self._base(service_id))
        return [EmbeddingPipeline.from_dict(p) for p in data.get("pipelines", [])]

    def create(
        self,
        service_id: str,
        *,
        database_name: str,
        source_table: str,
        text_columns: List[str],
        model_provider: str,
        embedding_model: str,
        model_dimensions: int,
        provider_api_key: str,
        source_schema: str = "",
        target_table: str = "",
        target_schema: str = "",
        provider_base_url: Optional[str] = None,
        batch_size: Optional[int] = None,
        poll_interval_seconds: Optional[int] = None,
        mode: Optional[str] = None,
        schedule_cron: Optional[str] = None,
        source_filter: Optional[str] = None,
        max_row_retries: Optional[int] = None,
    ) -> EmbeddingPipeline:
        """Create an embedding pipeline on a PostgreSQL service with pgvector.

        Setup is asynchronous: the returned pipeline starts in the configuring
        status; poll :meth:`get` until it is active.

        Args:
            service_id: ID of the PostgreSQL managed service.
            database_name: Database containing the source table.
            source_table: Table to embed.
            text_columns: Columns whose text content is concatenated and
                embedded.
            model_provider: Provider identifier, e.g. ``"openai"``.
            embedding_model: Model identifier, e.g. ``"text-embedding-3-small"``.
            model_dimensions: Output vector dimension (must match the model).
            provider_api_key: API key for the embedding provider (write-only).
            source_schema: Schema of the source table. Defaults to ``public``.
            target_table: Name of the companion vector table. Defaults to
                ``{source_table}_embeddings``.
            target_schema: Schema for the companion table.
            provider_base_url: Custom endpoint URL for self-hosted or
                compatible models.
            batch_size: Rows processed per embedding call. Defaults to 100.
            poll_interval_seconds: How often the continuous watcher polls.
            mode: ``"continuous"``, ``"scheduled"``, or ``"manual"``.
            schedule_cron: Five-field cron expression for scheduled mode.
            source_filter: SQL WHERE fragment to limit which rows are embedded.
            max_row_retries: Per-row retry limit before a row is skipped.
        """
        body: Dict[str, Any] = {
            "database_name": database_name,
            "source_table": source_table,
            "text_columns": text_columns,
            "model_provider": model_provider,
            "embedding_model": embedding_model,
            "model_dimensions": model_dimensions,
            "provider_api_key": provider_api_key,
        }
        if source_schema:
            body["source_schema"] = source_schema
        if target_table:
            body["target_table"] = target_table
        if target_schema:
            body["target_schema"] = target_schema
        if provider_base_url is not None:
            body["provider_base_url"] = provider_base_url
        if batch_size is not None:
            body["batch_size"] = batch_size
        if poll_interval_seconds is not None:
            body["poll_interval_seconds"] = poll_interval_seconds
        if mode is not None:
            body["mode"] = mode
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if source_filter is not None:
            body["source_filter"] = source_filter
        if max_row_retries is not None:
            body["max_row_retries"] = max_row_retries
        data = self._http.post(self._base(service_id), body)
        return EmbeddingPipeline.from_dict(data)

    def get(self, service_id: str, pipeline_id: str) -> Optional[EmbeddingPipeline]:
        """Return one embedding pipeline, or ``None`` when not found."""
        try:
            data = self._http.get(f"{self._base(service_id)}/{pipeline_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return EmbeddingPipeline.from_dict(data)

    def update(
        self,
        service_id: str,
        pipeline_id: str,
        *,
        embedding_model: Optional[str] = None,
        model_dimensions: Optional[int] = None,
        provider_api_key: Optional[str] = None,
        provider_base_url: Optional[str] = None,
        batch_size: Optional[int] = None,
        poll_interval_seconds: Optional[int] = None,
        mode: Optional[str] = None,
        schedule_cron: Optional[str] = None,
        source_filter: Optional[str] = None,
        max_row_retries: Optional[int] = None,
    ) -> EmbeddingPipeline:
        """Update the set fields of an embedding pipeline."""
        body: Dict[str, Any] = {}
        if embedding_model is not None:
            body["embedding_model"] = embedding_model
        if model_dimensions is not None:
            body["model_dimensions"] = model_dimensions
        if provider_api_key is not None:
            body["provider_api_key"] = provider_api_key
        if provider_base_url is not None:
            body["provider_base_url"] = provider_base_url
        if batch_size is not None:
            body["batch_size"] = batch_size
        if poll_interval_seconds is not None:
            body["poll_interval_seconds"] = poll_interval_seconds
        if mode is not None:
            body["mode"] = mode
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if source_filter is not None:
            body["source_filter"] = source_filter
        if max_row_retries is not None:
            body["max_row_retries"] = max_row_retries
        data = self._http.patch(f"{self._base(service_id)}/{pipeline_id}", body)
        return EmbeddingPipeline.from_dict(data)

    def delete(
        self,
        service_id: str,
        pipeline_id: str,
        *,
        remove_data: bool = False,
    ) -> None:
        """Delete an embedding pipeline.

        Args:
            service_id: ID of the PostgreSQL managed service.
            pipeline_id: ID of the pipeline.
            remove_data: When ``True``, the companion vector table is also
                dropped. When ``False`` (default) the embedded vectors are
                left in place.
        """
        path = f"{self._base(service_id)}/{pipeline_id}"
        if remove_data:
            path += "?remove_data=true"
        self._http.delete(path)

    def pause(self, service_id: str, pipeline_id: str) -> None:
        """Pause an active embedding pipeline."""
        self._http.post(f"{self._base(service_id)}/{pipeline_id}/pause")

    def resume(self, service_id: str, pipeline_id: str) -> None:
        """Resume a paused embedding pipeline."""
        self._http.post(f"{self._base(service_id)}/{pipeline_id}/resume")

    # ------------------------------------------------------------------
    # Runs (scheduled / manual pipelines)
    # ------------------------------------------------------------------

    def trigger_run(
        self, service_id: str, pipeline_id: str
    ) -> EmbeddingPipelineRun:
        """Enqueue one manual run for a scheduled or manual pipeline.

        Continuous pipelines have no discrete runs and reject this call.
        Poll :meth:`get_run` until the run reaches a terminal status.
        """
        data = self._http.post(f"{self._base(service_id)}/{pipeline_id}/runs")
        return EmbeddingPipelineRun.from_dict(data)

    def list_runs(
        self, service_id: str, pipeline_id: str
    ) -> List[EmbeddingPipelineRun]:
        """Return the latest runs of a pipeline, newest first."""
        data = self._http.get(f"{self._base(service_id)}/{pipeline_id}/runs")
        return [EmbeddingPipelineRun.from_dict(r) for r in data.get("runs", [])]

    def get_run(
        self, service_id: str, pipeline_id: str, run_id: str
    ) -> Optional[EmbeddingPipelineRun]:
        """Return one run, or ``None`` when not found."""
        try:
            data = self._http.get(
                f"{self._base(service_id)}/{pipeline_id}/runs/{run_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return EmbeddingPipelineRun.from_dict(data)


class AsyncEmbeddingPipelinesAPI:
    """Manages embedding pipelines on PostgreSQL services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    @staticmethod
    def _base(service_id: str) -> str:
        return f"/managed-services/{service_id}/embedding-pipelines"

    async def list(self, service_id: str) -> List[EmbeddingPipeline]:
        """Return all embedding pipelines on the service."""
        data = await self._http.get(self._base(service_id))
        return [EmbeddingPipeline.from_dict(p) for p in data.get("pipelines", [])]

    async def create(
        self,
        service_id: str,
        *,
        database_name: str,
        source_table: str,
        text_columns: List[str],
        model_provider: str,
        embedding_model: str,
        model_dimensions: int,
        provider_api_key: str,
        source_schema: str = "",
        target_table: str = "",
        target_schema: str = "",
        provider_base_url: Optional[str] = None,
        batch_size: Optional[int] = None,
        poll_interval_seconds: Optional[int] = None,
        mode: Optional[str] = None,
        schedule_cron: Optional[str] = None,
        source_filter: Optional[str] = None,
        max_row_retries: Optional[int] = None,
    ) -> EmbeddingPipeline:
        """Create an embedding pipeline on a PostgreSQL service with pgvector."""
        body: Dict[str, Any] = {
            "database_name": database_name,
            "source_table": source_table,
            "text_columns": text_columns,
            "model_provider": model_provider,
            "embedding_model": embedding_model,
            "model_dimensions": model_dimensions,
            "provider_api_key": provider_api_key,
        }
        if source_schema:
            body["source_schema"] = source_schema
        if target_table:
            body["target_table"] = target_table
        if target_schema:
            body["target_schema"] = target_schema
        if provider_base_url is not None:
            body["provider_base_url"] = provider_base_url
        if batch_size is not None:
            body["batch_size"] = batch_size
        if poll_interval_seconds is not None:
            body["poll_interval_seconds"] = poll_interval_seconds
        if mode is not None:
            body["mode"] = mode
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if source_filter is not None:
            body["source_filter"] = source_filter
        if max_row_retries is not None:
            body["max_row_retries"] = max_row_retries
        data = await self._http.post(self._base(service_id), body)
        return EmbeddingPipeline.from_dict(data)

    async def get(self, service_id: str, pipeline_id: str) -> Optional[EmbeddingPipeline]:
        """Return one embedding pipeline, or ``None`` when not found."""
        try:
            data = await self._http.get(f"{self._base(service_id)}/{pipeline_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return EmbeddingPipeline.from_dict(data)

    async def update(
        self,
        service_id: str,
        pipeline_id: str,
        *,
        embedding_model: Optional[str] = None,
        model_dimensions: Optional[int] = None,
        provider_api_key: Optional[str] = None,
        provider_base_url: Optional[str] = None,
        batch_size: Optional[int] = None,
        poll_interval_seconds: Optional[int] = None,
        mode: Optional[str] = None,
        schedule_cron: Optional[str] = None,
        source_filter: Optional[str] = None,
        max_row_retries: Optional[int] = None,
    ) -> EmbeddingPipeline:
        """Update the set fields of an embedding pipeline."""
        body: Dict[str, Any] = {}
        if embedding_model is not None:
            body["embedding_model"] = embedding_model
        if model_dimensions is not None:
            body["model_dimensions"] = model_dimensions
        if provider_api_key is not None:
            body["provider_api_key"] = provider_api_key
        if provider_base_url is not None:
            body["provider_base_url"] = provider_base_url
        if batch_size is not None:
            body["batch_size"] = batch_size
        if poll_interval_seconds is not None:
            body["poll_interval_seconds"] = poll_interval_seconds
        if mode is not None:
            body["mode"] = mode
        if schedule_cron is not None:
            body["schedule_cron"] = schedule_cron
        if source_filter is not None:
            body["source_filter"] = source_filter
        if max_row_retries is not None:
            body["max_row_retries"] = max_row_retries
        data = await self._http.patch(f"{self._base(service_id)}/{pipeline_id}", body)
        return EmbeddingPipeline.from_dict(data)

    async def delete(
        self,
        service_id: str,
        pipeline_id: str,
        *,
        remove_data: bool = False,
    ) -> None:
        """Delete an embedding pipeline."""
        path = f"{self._base(service_id)}/{pipeline_id}"
        if remove_data:
            path += "?remove_data=true"
        await self._http.delete(path)

    async def pause(self, service_id: str, pipeline_id: str) -> None:
        """Pause an active embedding pipeline."""
        await self._http.post(f"{self._base(service_id)}/{pipeline_id}/pause")

    async def resume(self, service_id: str, pipeline_id: str) -> None:
        """Resume a paused embedding pipeline."""
        await self._http.post(f"{self._base(service_id)}/{pipeline_id}/resume")

    async def trigger_run(
        self, service_id: str, pipeline_id: str
    ) -> EmbeddingPipelineRun:
        """Enqueue one manual run for a scheduled or manual pipeline."""
        data = await self._http.post(f"{self._base(service_id)}/{pipeline_id}/runs")
        return EmbeddingPipelineRun.from_dict(data)

    async def list_runs(
        self, service_id: str, pipeline_id: str
    ) -> List[EmbeddingPipelineRun]:
        """Return the latest runs of a pipeline, newest first."""
        data = await self._http.get(f"{self._base(service_id)}/{pipeline_id}/runs")
        return [EmbeddingPipelineRun.from_dict(r) for r in data.get("runs", [])]

    async def get_run(
        self, service_id: str, pipeline_id: str, run_id: str
    ) -> Optional[EmbeddingPipelineRun]:
        """Return one run, or ``None`` when not found."""
        try:
            data = await self._http.get(
                f"{self._base(service_id)}/{pipeline_id}/runs/{run_id}"
            )
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return EmbeddingPipelineRun.from_dict(data)
