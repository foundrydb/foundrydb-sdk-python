"""
FoundryDB SDK - Vector Search API (sync and async).

Typed, read-only similarity search over pgvector columns, brokered through
the platform's read-only data plane. The controller composes the SQL from
validated inputs; results are row-capped.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import VectorSearchFilter, VectorSearchResponse


class VectorSearchAPI:
    """Runs vector similarity searches against PostgreSQL services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def search(
        self,
        service_id: str,
        *,
        database_name: str,
        table: str,
        vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        schema: str = "",
        embedding_column: str = "",
        top_k: int = 0,
        metric: str = "",
        filters: Optional[List[VectorSearchFilter]] = None,
        include_columns: Optional[List[str]] = None,
    ) -> VectorSearchResponse:
        """Run a read-only pgvector similarity search.

        Exactly one of ``vector`` or ``query_text`` must be set. When
        ``query_text`` is provided, ``pipeline_id`` is also required so the
        platform embeds the text with the same provider, model, and dimensions
        that produced the indexed vectors.

        Args:
            service_id: ID of the PostgreSQL managed service.
            database_name: Database containing the table.
            table: Table name to search.
            vector: Pre-computed query vector. Mutually exclusive with
                ``query_text``.
            query_text: Natural-language query to embed before searching.
                Mutually exclusive with ``vector``.
            pipeline_id: ID of the embedding pipeline to use for ``query_text``
                embedding. Required when ``query_text`` is set.
            schema: Table schema. Defaults to ``public``.
            embedding_column: Name of the pgvector column. Inferred when
                omitted.
            top_k: Maximum number of results to return. Defaults to 10.
            metric: Distance metric: ``"cosine"`` (default), ``"l2"``, or
                ``"ip"``.
            filters: Column equality filters applied to the search.
            include_columns: Columns to include in each result row. Defaults
                to all non-vector columns.
        """
        body: Dict[str, Any] = {
            "database_name": database_name,
            "table": table,
        }
        if vector is not None:
            body["vector"] = vector
        if query_text is not None:
            body["query_text"] = query_text
        if pipeline_id is not None:
            body["pipeline_id"] = pipeline_id
        if schema:
            body["schema"] = schema
        if embedding_column:
            body["embedding_column"] = embedding_column
        if top_k > 0:
            body["top_k"] = top_k
        if metric:
            body["metric"] = metric
        if filters:
            body["filters"] = [f.to_dict() for f in filters]
        if include_columns:
            body["include_columns"] = include_columns
        data = self._http.post(
            f"/managed-services/{service_id}/vector-search", body
        )
        return VectorSearchResponse.from_dict(data)


class AsyncVectorSearchAPI:
    """Runs vector similarity searches against PostgreSQL services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def search(
        self,
        service_id: str,
        *,
        database_name: str,
        table: str,
        vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        schema: str = "",
        embedding_column: str = "",
        top_k: int = 0,
        metric: str = "",
        filters: Optional[List[VectorSearchFilter]] = None,
        include_columns: Optional[List[str]] = None,
    ) -> VectorSearchResponse:
        """Run a read-only pgvector similarity search."""
        body: Dict[str, Any] = {
            "database_name": database_name,
            "table": table,
        }
        if vector is not None:
            body["vector"] = vector
        if query_text is not None:
            body["query_text"] = query_text
        if pipeline_id is not None:
            body["pipeline_id"] = pipeline_id
        if schema:
            body["schema"] = schema
        if embedding_column:
            body["embedding_column"] = embedding_column
        if top_k > 0:
            body["top_k"] = top_k
        if metric:
            body["metric"] = metric
        if filters:
            body["filters"] = [f.to_dict() for f in filters]
        if include_columns:
            body["include_columns"] = include_columns
        data = await self._http.post(
            f"/managed-services/{service_id}/vector-search", body
        )
        return VectorSearchResponse.from_dict(data)
