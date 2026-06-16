"""
FoundryDB SDK - File Services API (sync and async).

File services are managed S3-compatible object storage buckets with scoped
access keys, presigned URLs, and quota enforcement. Provisioning is
asynchronous: a new service starts in Pending and reaches Running once the
bucket is ready.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    FilesService,
    FilesAccessKey,
    FilesAccessKeyWithSecret,
    FilesPresignedURL,
    FilesObjectPage,
)


class FileServicesAPI:
    """Manages file services (object storage) (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Service lifecycle
    # ------------------------------------------------------------------

    def list(self) -> List[FilesService]:
        """Return all file services visible to the authenticated user."""
        data = self._http.get("/file-services")
        return [FilesService.from_dict(s) for s in data.get("file_services", [])]

    def get(self, service_id: str) -> Optional[FilesService]:
        """Return a file service by ID, or ``None`` when not found."""
        try:
            data = self._http.get(f"/file-services/{service_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return FilesService.from_dict(data)

    def create(
        self,
        *,
        name: str,
        zone: str = "",
        quota_gb_soft: Optional[int] = None,
        quota_gb_hard: Optional[int] = None,
        organization_id: Optional[str] = None,
    ) -> FilesService:
        """Provision a new file service.

        The service is created in the Pending status and reaches Running once
        the bucket is provisioned.

        Args:
            name: Display name for the service.
            zone: Provider region for the bucket. Empty uses the platform
                default.
            quota_gb_soft: Stored-GB threshold that triggers a notification.
            quota_gb_hard: Stored-GB ceiling; uploads are blocked once
                exceeded.
            organization_id: Assign the service to an organization.
        """
        body: Dict[str, Any] = {"name": name}
        if zone:
            body["zone"] = zone
        if quota_gb_soft is not None:
            body["quota_gb_soft"] = quota_gb_soft
        if quota_gb_hard is not None:
            body["quota_gb_hard"] = quota_gb_hard
        if organization_id:
            body["organization_id"] = organization_id
        data = self._http.post("/file-services", body)
        return FilesService.from_dict(data)

    def delete(self, service_id: str) -> None:
        """Delete a file service and all its bucket contents.

        Idempotent: a 404 response is treated as success.
        """
        try:
            self._http.delete(f"/file-services/{service_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return
            raise

    # ------------------------------------------------------------------
    # Access keys
    # ------------------------------------------------------------------

    def create_access_key(
        self,
        service_id: str,
        *,
        name: str,
        permissions: str,
        prefix: str = "",
    ) -> FilesAccessKeyWithSecret:
        """Mint a new scoped S3 credential.

        The secret access key is returned exactly once in this response;
        store it immediately. Key creation is blocked while the service is
        over its hard storage quota.

        Args:
            service_id: ID of the file service.
            name: Human-readable label for the key.
            permissions: ``"read"``, ``"write"``, or ``"readwrite"``.
            prefix: Object key prefix the credential is scoped to. Empty
                grants the whole bucket.
        """
        body: Dict[str, Any] = {"name": name, "permissions": permissions}
        if prefix:
            body["prefix"] = prefix
        data = self._http.post(f"/file-services/{service_id}/keys", body)
        return FilesAccessKeyWithSecret.from_dict(data)

    def list_access_keys(self, service_id: str) -> List[FilesAccessKey]:
        """Return the service's access keys (no secret halves)."""
        data = self._http.get(f"/file-services/{service_id}/keys")
        return [FilesAccessKey.from_dict(k) for k in data.get("keys", [])]

    def revoke_access_key(self, service_id: str, key_id: str) -> None:
        """Revoke one access key. Revocation is permanent and immediate."""
        self._http.delete(f"/file-services/{service_id}/keys/{key_id}")

    # ------------------------------------------------------------------
    # Presigned URLs
    # ------------------------------------------------------------------

    def presign(
        self,
        service_id: str,
        *,
        method: str,
        key: str,
        expires_seconds: int = 0,
        content_type: str = "",
    ) -> FilesPresignedURL:
        """Presign one S3 operation and return the URL.

        The URL is used directly against the bucket endpoint without further
        credentials, until it expires. Upload (PUT) presigning is blocked
        while the service is over its hard storage quota.

        Args:
            service_id: ID of the file service.
            method: HTTP method to presign: ``GET``, ``PUT``, ``HEAD``, or
                ``DELETE`` (uppercase).
            key: Object key the URL operates on.
            expires_seconds: URL lifetime; 0 applies the platform default
                (15 minutes), maximum is 604800 (7 days).
            content_type: When set on a PUT, signed into the URL so the
                upload must send the same Content-Type header.
        """
        body: Dict[str, Any] = {"method": method, "key": key}
        if expires_seconds > 0:
            body["expires_seconds"] = expires_seconds
        if content_type:
            body["content_type"] = content_type
        data = self._http.post(f"/file-services/{service_id}/presign", body)
        return FilesPresignedURL.from_dict(data)

    # ------------------------------------------------------------------
    # Object listing
    # ------------------------------------------------------------------

    def list_objects(
        self,
        service_id: str,
        *,
        prefix: str = "",
        cursor: str = "",
        max: int = 0,
    ) -> FilesObjectPage:
        """Return one page of the bucket's objects.

        Args:
            service_id: ID of the file service.
            prefix: Filter to objects whose key starts with this prefix.
            cursor: ``next_cursor`` from a previous page to continue listing.
            max: Page size cap (0 applies the server default of 100, maximum
                is 1000).
        """
        params: Dict[str, Any] = {}
        if prefix:
            params["prefix"] = prefix
        if cursor:
            params["cursor"] = cursor
        if max > 0:
            params["max"] = max
        data = self._http.get(
            f"/file-services/{service_id}/objects",
            params=params or None,
        )
        return FilesObjectPage.from_dict(data)

    def delete_object(self, service_id: str, key: str) -> None:
        """Remove one object from the service's bucket."""
        self._http.delete(f"/file-services/{service_id}/objects?key={key}")


class AsyncFileServicesAPI:
    """Manages file services (object storage) (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(self) -> List[FilesService]:
        """Return all file services visible to the authenticated user."""
        data = await self._http.get("/file-services")
        return [FilesService.from_dict(s) for s in data.get("file_services", [])]

    async def get(self, service_id: str) -> Optional[FilesService]:
        """Return a file service by ID, or ``None`` when not found."""
        try:
            data = await self._http.get(f"/file-services/{service_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return FilesService.from_dict(data)

    async def create(
        self,
        *,
        name: str,
        zone: str = "",
        quota_gb_soft: Optional[int] = None,
        quota_gb_hard: Optional[int] = None,
        organization_id: Optional[str] = None,
    ) -> FilesService:
        """Provision a new file service."""
        body: Dict[str, Any] = {"name": name}
        if zone:
            body["zone"] = zone
        if quota_gb_soft is not None:
            body["quota_gb_soft"] = quota_gb_soft
        if quota_gb_hard is not None:
            body["quota_gb_hard"] = quota_gb_hard
        if organization_id:
            body["organization_id"] = organization_id
        data = await self._http.post("/file-services", body)
        return FilesService.from_dict(data)

    async def delete(self, service_id: str) -> None:
        """Delete a file service and all its bucket contents (idempotent)."""
        try:
            await self._http.delete(f"/file-services/{service_id}")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return
            raise

    async def create_access_key(
        self,
        service_id: str,
        *,
        name: str,
        permissions: str,
        prefix: str = "",
    ) -> FilesAccessKeyWithSecret:
        """Mint a new scoped S3 credential."""
        body: Dict[str, Any] = {"name": name, "permissions": permissions}
        if prefix:
            body["prefix"] = prefix
        data = await self._http.post(f"/file-services/{service_id}/keys", body)
        return FilesAccessKeyWithSecret.from_dict(data)

    async def list_access_keys(self, service_id: str) -> List[FilesAccessKey]:
        """Return the service's access keys (no secret halves)."""
        data = await self._http.get(f"/file-services/{service_id}/keys")
        return [FilesAccessKey.from_dict(k) for k in data.get("keys", [])]

    async def revoke_access_key(self, service_id: str, key_id: str) -> None:
        """Revoke one access key."""
        await self._http.delete(f"/file-services/{service_id}/keys/{key_id}")

    async def presign(
        self,
        service_id: str,
        *,
        method: str,
        key: str,
        expires_seconds: int = 0,
        content_type: str = "",
    ) -> FilesPresignedURL:
        """Presign one S3 operation and return the URL."""
        body: Dict[str, Any] = {"method": method, "key": key}
        if expires_seconds > 0:
            body["expires_seconds"] = expires_seconds
        if content_type:
            body["content_type"] = content_type
        data = await self._http.post(f"/file-services/{service_id}/presign", body)
        return FilesPresignedURL.from_dict(data)

    async def list_objects(
        self,
        service_id: str,
        *,
        prefix: str = "",
        cursor: str = "",
        max: int = 0,
    ) -> FilesObjectPage:
        """Return one page of the bucket's objects."""
        params: Dict[str, Any] = {}
        if prefix:
            params["prefix"] = prefix
        if cursor:
            params["cursor"] = cursor
        if max > 0:
            params["max"] = max
        data = await self._http.get(
            f"/file-services/{service_id}/objects",
            params=params or None,
        )
        return FilesObjectPage.from_dict(data)

    async def delete_object(self, service_id: str, key: str) -> None:
        """Remove one object from the service's bucket."""
        await self._http.delete(f"/file-services/{service_id}/objects?key={key}")
