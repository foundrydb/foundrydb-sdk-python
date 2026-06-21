"""
FoundryDB SDK - Companion-app attachments API (sync and async).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional  # noqa: F401

from .client import HTTPClient, AsyncHTTPClient
from .types import AppService, AttachmentCatalogEntry, AttachmentCredentials, AttachmentSummary


class AttachmentsAPI:
    """Companion-app attachment operations (sync).

    Attachments are thin wrappers over app-hosting that click-to-attach a
    pre-configured companion application (e.g. Metabase, Directus) to an
    existing managed database service. The companion app is provisioned,
    wired to the parent service, and made accessible via ``url``.
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_catalog(self) -> List[AttachmentCatalogEntry]:
        """Return the catalog of available companion-app attachment kinds.

        Each entry describes one kind of companion app that can be attached
        to a managed service, including which database engine types it
        supports via ``requires_parent_kinds``.
        """
        data = self._http.get("/attachment-catalog")
        return [AttachmentCatalogEntry.from_dict(e) for e in data.get("catalog", [])]

    def create(
        self,
        parent_service_id: str,
        *,
        kind: str,
        plan_name: Optional[str] = None,
        subdomain: Optional[str] = None,
    ) -> AppService:
        """Attach a companion app to a managed service.

        Provisions the companion app, wires it to ``parent_service_id``, and
        returns the resulting ``AppService``. The app moves through the normal
        app-service lifecycle states; poll ``list`` until ``status`` is
        ``"Running"``.

        Args:
            parent_service_id: ID of the managed database service to attach to.
            kind: Companion-app kind from the catalog (e.g. ``"metabase"``).
            plan_name: Compute plan for the companion app. Defaults to the
                catalog entry's ``default_plan`` when omitted.
            subdomain: Optional custom subdomain for the companion app's URL.
        """
        body: Dict[str, Any] = {"kind": kind}
        if plan_name is not None:
            body["plan_name"] = plan_name
        if subdomain is not None:
            body["subdomain"] = subdomain
        data = self._http.post(f"/managed-services/{parent_service_id}/attachments", body)
        return AppService.from_dict(data)

    def list(self, parent_service_id: str) -> List[AttachmentSummary]:
        """List all companion-app attachments on a managed service.

        Args:
            parent_service_id: ID of the managed database service.
        """
        data = self._http.get(f"/managed-services/{parent_service_id}/attachments")
        return [AttachmentSummary.from_dict(a) for a in data.get("attachments", [])]

    def get_credentials(self, app_service_id: str) -> AttachmentCredentials:
        """Retrieve the admin credentials for a companion-app attachment.

        ``admin_email`` and ``admin_password`` can be used to log into the
        companion app's own admin UI. ``generated`` holds any additional
        key/value pairs exposed by the specific companion app (API tokens,
        embed secrets, etc.).

        Args:
            app_service_id: ID of the companion app service (from
                ``AttachmentSummary.app_service_id`` or the ``AppService``
                returned by ``create``).
        """
        data = self._http.get(f"/app-services/{app_service_id}/attachment-credentials")
        return AttachmentCredentials.from_dict(data)


class AsyncAttachmentsAPI:
    """Companion-app attachment operations (async).

    Attachments are thin wrappers over app-hosting that click-to-attach a
    pre-configured companion application (e.g. Metabase, Directus) to an
    existing managed database service. The companion app is provisioned,
    wired to the parent service, and made accessible via ``url``.
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_catalog(self) -> List[AttachmentCatalogEntry]:
        """Return the catalog of available companion-app attachment kinds.

        Each entry describes one kind of companion app that can be attached
        to a managed service, including which database engine types it
        supports via ``requires_parent_kinds``.
        """
        data = await self._http.get("/attachment-catalog")
        return [AttachmentCatalogEntry.from_dict(e) for e in data.get("catalog", [])]

    async def create(
        self,
        parent_service_id: str,
        *,
        kind: str,
        plan_name: Optional[str] = None,
        subdomain: Optional[str] = None,
    ) -> AppService:
        """Attach a companion app to a managed service.

        Provisions the companion app, wires it to ``parent_service_id``, and
        returns the resulting ``AppService``. The app moves through the normal
        app-service lifecycle states; poll ``list`` until ``status`` is
        ``"Running"``.

        Args:
            parent_service_id: ID of the managed database service to attach to.
            kind: Companion-app kind from the catalog (e.g. ``"metabase"``).
            plan_name: Compute plan for the companion app. Defaults to the
                catalog entry's ``default_plan`` when omitted.
            subdomain: Optional custom subdomain for the companion app's URL.
        """
        body: Dict[str, Any] = {"kind": kind}
        if plan_name is not None:
            body["plan_name"] = plan_name
        if subdomain is not None:
            body["subdomain"] = subdomain
        data = await self._http.post(
            f"/managed-services/{parent_service_id}/attachments", body
        )
        return AppService.from_dict(data)

    async def list(self, parent_service_id: str) -> List[AttachmentSummary]:
        """List all companion-app attachments on a managed service.

        Args:
            parent_service_id: ID of the managed database service.
        """
        data = await self._http.get(f"/managed-services/{parent_service_id}/attachments")
        return [AttachmentSummary.from_dict(a) for a in data.get("attachments", [])]

    async def get_credentials(self, app_service_id: str) -> AttachmentCredentials:
        """Retrieve the admin credentials for a companion-app attachment.

        ``admin_email`` and ``admin_password`` can be used to log into the
        companion app's own admin UI. ``generated`` holds any additional
        key/value pairs exposed by the specific companion app (API tokens,
        embed secrets, etc.).

        Args:
            app_service_id: ID of the companion app service (from
                ``AttachmentSummary.app_service_id`` or the ``AppService``
                returned by ``create``).
        """
        data = await self._http.get(
            f"/app-services/{app_service_id}/attachment-credentials"
        )
        return AttachmentCredentials.from_dict(data)
