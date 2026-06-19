"""
FoundryDB SDK - App Services API (sync and async).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional  # noqa: F401

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    AppContainerConfig,
    AppDeployment,
    AppService,
    AuthConfigurationWithKeys,
    AuthEnableRequest,
    AuthSigningKey,
    IdpProviderConfig,
)


class AppServicesAPI:
    """Manages FoundryDB app services (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self) -> List[AppService]:
        """List all app services."""
        data = self._http.get("/app-services")
        return [AppService.from_dict(a) for a in data.get("app_services", [])]

    def create(
        self,
        *,
        name: str,
        plan_name: str,
        app_config: AppContainerConfig,
        zone: Optional[str] = None,
        storage_size_gb: int = 10,
        storage_tier: str = "maxiops",
        attached_service_ids: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
    ) -> AppService:
        """Create a new app service.

        Args:
            name: Display name for the app.
            plan_name: Compute plan identifier (e.g. "tier-2").
            app_config: Container image and port configuration.
            zone: Deployment zone (e.g. "se-sto1").
            storage_size_gb: Size of the data disk in gigabytes (minimum 10).
            storage_tier: Storage performance tier ("standard" or "maxiops").
            attached_service_ids: Managed service IDs to attach at creation time.
            organization_id: Optional org ID for this request.
        """
        body: Dict[str, Any] = {
            "name": name,
            "plan_name": plan_name,
            "app_config": app_config.to_dict(),
            "storage_size_gb": storage_size_gb,
            "storage_tier": storage_tier,
        }
        if zone is not None:
            body["zone"] = zone
        if attached_service_ids:
            body["attached_service_ids"] = attached_service_ids
        if organization_id is not None:
            body["organization_id"] = organization_id
        extra_headers: Dict[str, str] = {}
        if organization_id:
            extra_headers["X-Active-Org-ID"] = organization_id
        data = self._http.post("/app-services", body, extra_headers=extra_headers or None)
        return AppService.from_dict(data)

    def get(self, app_service_id: str) -> AppService:
        """Get an app service by ID."""
        data = self._http.get(f"/app-services/{app_service_id}")
        return AppService.from_dict(data)

    def update(self, app_service_id: str, *, app_config: AppContainerConfig) -> AppService:
        """Update an app service's container configuration.

        A changed image reference or environment triggers a zero-downtime
        blue/green redeploy.
        """
        body: Dict[str, Any] = {"app_config": app_config.to_dict()}
        data = self._http.patch(f"/app-services/{app_service_id}", body)
        return AppService.from_dict(data)

    def delete(self, app_service_id: str) -> None:
        """Delete an app service."""
        self._http.delete(f"/app-services/{app_service_id}")

    def restart(self, app_service_id: str) -> None:
        """Restart the app's running container in place."""
        self._http.post(f"/app-services/{app_service_id}/restart")

    def scale(self, app_service_id: str, *, plan_name: str) -> AppService:
        """Change the app's compute plan.

        Scaling up uses a zero-downtime hot resize; scaling down may incur a
        brief restart.
        """
        body: Dict[str, Any] = {"plan_name": plan_name}
        data = self._http.post(f"/app-services/{app_service_id}/scale", body)
        return AppService.from_dict(data)

    def attach(self, app_service_id: str, *, attached_service_id: str) -> AppService:
        """Attach a managed service to a running app.

        The target may be a database or another app (east-west app-to-app).
        The platform peers the private networks, opens the target's port to the
        app's subnet, and rolls a zero-downtime redeploy so the injected
        environment is updated: a database injects connection credentials; an
        app injects ``MDB_<NAME>_HOST/PORT/URL`` for plain-HTTP calls over the
        private SDN (no credentials, no ``DATABASE_URL``). An app supports up
        to five attachments (databases and apps combined). The target must be
        Running, owned by the same user, in the app's peering region, and not
        the app itself.

        Args:
            app_service_id: ID of the app service to attach to.
            attached_service_id: ID of the database or app service to attach.
        """
        body: Dict[str, Any] = {"attached_service_id": attached_service_id}
        data = self._http.post(f"/app-services/{app_service_id}/attachments", body)
        return AppService.from_dict(data)

    def detach(self, app_service_id: str, attachment_id: str) -> AppService:
        """Remove an attachment from a running app."""
        data = self._http.delete(f"/app-services/{app_service_id}/attachments/{attachment_id}")  # type: ignore[assignment]
        if data is None:
            return self.get(app_service_id)
        return AppService.from_dict(data)

    # ------------------------------------------------------------------
    # Deployment history
    # ------------------------------------------------------------------

    def list_deployments(self, app_service_id: str) -> List[AppDeployment]:
        """List the deploy history of an app service, newest first.

        Each entry is a previously rolled-out image and configuration.
        ``deploy_logs`` on each entry holds the ordered steps the agent
        executed for that revision (image start, health probe, ingress
        cutover, previous-color teardown).

        Args:
            app_service_id: ID of the app service.
        """
        data = self._http.get(f"/app-services/{app_service_id}/deployments")
        return [AppDeployment.from_dict(d) for d in data.get("deployments", [])]

    def rollback(self, app_service_id: str, *, deployment_id: str) -> AppService:
        """Redeploy an earlier revision via a zero-downtime blue/green swap.

        Args:
            app_service_id: ID of the app service.
            deployment_id: ID of the deployment to roll back to (from
                ``list_deployments``).
        """
        body: Dict[str, Any] = {"deployment_id": deployment_id}
        data = self._http.post(f"/app-services/{app_service_id}/rollback", body)
        return AppService.from_dict(data)

    # ------------------------------------------------------------------
    # Auth methods
    # ------------------------------------------------------------------

    def enable_app_service_auth(
        self, app_service_id: str, req: AuthEnableRequest
    ) -> AuthConfigurationWithKeys:
        """Enable end-user authentication for an app service.

        Provisions a managed OIDC identity provider backed by one of the app's
        attached PostgreSQL services. SMTP credentials in the request are stored
        in the platform secret store and never returned. To enable social login
        (Google or GitHub) populate ``req.idp_providers``; each provider's
        client secret is stored in the secret store and never returned.

        Args:
            app_service_id: ID of the app service to enable auth for.
            req: Auth enable parameters including SMTP credentials, optional
                branding theme, and optional social-login providers.

        Returns:
            The auth configuration and its signing key records.
        """
        data = self._http.post(
            f"/app-services/{app_service_id}/auth/enable", req.to_dict()
        )
        return AuthConfigurationWithKeys.from_dict(data)

    def get_app_service_auth(self, app_service_id: str) -> Optional[AuthConfigurationWithKeys]:
        """Get the auth configuration for an app service.

        Returns ``None`` when auth is not enabled (404 from the API).

        Args:
            app_service_id: ID of the app service.

        Returns:
            The auth configuration and signing key records, or ``None`` if auth
            is not enabled.
        """
        try:
            data = self._http.get(f"/app-services/{app_service_id}/auth")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return AuthConfigurationWithKeys.from_dict(data)

    def disable_app_service_auth(self, app_service_id: str) -> str:
        """Disable end-user authentication for an app service.

        Tears down the managed issuer and marks the auth configuration
        ``Disabled``. The end-user identity data in the customer's database is
        left untouched.

        Args:
            app_service_id: ID of the app service.

        Returns:
            The new status string (``"Disabled"``).
        """
        data = self._http.post(f"/app-services/{app_service_id}/auth/disable")
        return data.get("status", "Disabled") if data else "Disabled"

    def rotate_app_service_auth_key(self, app_service_id: str) -> AuthSigningKey:
        """Rotate the JWT signing key for an app service's auth.

        Rotation is dual-kid: the new key is published alongside the outgoing
        one so tokens signed by the previous key keep validating until it
        retires. Key material is held in the platform secret store and never
        returned.

        Args:
            app_service_id: ID of the app service.

        Returns:
            The newly minted signing key record.
        """
        data = self._http.post(f"/app-services/{app_service_id}/auth/rotate-key")
        return AuthSigningKey.from_dict(data.get("signing_key", {}))

    def revoke_app_service_auth_session(
        self, app_service_id: str, session_id: str
    ) -> str:
        """Revoke one end-user session.

        The revocation is dispatched asynchronously to the backing database's
        primary VM and applied in the customer's identity schema.

        Args:
            app_service_id: ID of the app service.
            session_id: The end-user session id to revoke.

        Returns:
            The dispatched task id.
        """
        data = self._http.post(
            f"/app-services/{app_service_id}/auth/sessions/{session_id}/revoke"
        )
        return data.get("task_id", "") if data else ""

    def delete_app_service_auth_user(
        self,
        app_service_id: str,
        *,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Erase one end-user under the GDPR right to erasure (Art. 17).

        Exactly one of ``email`` or ``user_id`` must be supplied. The erasure
        removes the user and their identity data (identities, sessions, refresh
        tokens, MFA enrolments, pending login/oauth tokens) and scrubs the
        user's audit-log rows. It is dispatched asynchronously to the backing
        database's primary VM.

        Args:
            app_service_id: ID of the app service.
            email: Address the end-user by email. Mutually exclusive with
                ``user_id``.
            user_id: Address the end-user by their auth subject UUID. Mutually
                exclusive with ``email``.

        Returns:
            The dispatched task id for status polling.
        """
        if not email and not user_id:
            raise ValueError("Exactly one of email or user_id must be provided")
        body: Dict[str, Any] = {}
        if email:
            body["email"] = email
        if user_id:
            body["user_id"] = user_id
        data = self._http.post(
            f"/app-services/{app_service_id}/auth/users/delete", body
        )
        return data.get("task_id", "") if data else ""

    def delete_app_service_auth_user_by_identifier(
        self, app_service_id: str, identifier: str
    ) -> str:
        """Erase one end-user by identifier via DELETE
        /app-services/{id}/auth/users/{identifier}.

        The identifier is an opaque string addressing the user (typically
        their subject UUID or encoded email). The erasure semantics are
        identical to ``delete_app_service_auth_user``.

        Args:
            app_service_id: ID of the app service.
            identifier: The user identifier to erase.

        Returns:
            The dispatched task id for status polling.
        """
        data = self._http.delete(
            f"/app-services/{app_service_id}/auth/users/{identifier}"
        )
        return data.get("task_id", "") if data else ""  # type: ignore[union-attr]

    def list_auth_providers(self, app_service_id: str) -> List[IdpProviderConfig]:
        """List the social-login providers configured for an app service's auth.

        Returns the non-secret portion of each provider record. Client secrets
        are custodied in the platform secret store and are never returned.

        Args:
            app_service_id: ID of the app service.

        Returns:
            The list of configured social-login providers.
        """
        data = self._http.get(f"/app-services/{app_service_id}/auth/providers")
        return [IdpProviderConfig.from_dict(p) for p in data.get("providers", [])]

    def upsert_auth_provider(
        self,
        app_service_id: str,
        provider: str,
        *,
        client_id: str,
        client_secret: str,
        display_name: Optional[str] = None,
    ) -> List[IdpProviderConfig]:
        """Add or update a social-login provider for an app service's auth.

        The ``client_secret`` is write-only: it is stored in the platform
        secret store and never returned in any response.

        Args:
            app_service_id: ID of the app service.
            provider: Provider identifier (e.g. ``"google"`` or ``"github"``).
            client_id: OAuth2 client ID issued by the provider.
            client_secret: OAuth2 client secret issued by the provider. Stored
                in the secret store; never logged or returned.
            display_name: Optional human-readable label shown on the login UI.

        Returns:
            The updated list of all configured social-login providers.
        """
        body: Dict[str, Any] = {
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if display_name is not None:
            body["display_name"] = display_name
        data = self._http.put(
            f"/app-services/{app_service_id}/auth/providers/{provider}", body
        )
        return [IdpProviderConfig.from_dict(p) for p in data.get("providers", [])]

    def remove_auth_provider(
        self, app_service_id: str, provider: str
    ) -> List[IdpProviderConfig]:
        """Remove a social-login provider from an app service's auth.

        Args:
            app_service_id: ID of the app service.
            provider: Provider identifier to remove (e.g. ``"google"``).

        Returns:
            The remaining list of configured social-login providers.
        """
        data = self._http.delete(
            f"/app-services/{app_service_id}/auth/providers/{provider}"
        )
        return [IdpProviderConfig.from_dict(p) for p in data.get("providers", [])]  # type: ignore[union-attr]


class AsyncAppServicesAPI:
    """Manages FoundryDB app services (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(self) -> List[AppService]:
        """List all app services."""
        data = await self._http.get("/app-services")
        return [AppService.from_dict(a) for a in data.get("app_services", [])]

    async def create(
        self,
        *,
        name: str,
        plan_name: str,
        app_config: AppContainerConfig,
        zone: Optional[str] = None,
        storage_size_gb: int = 10,
        storage_tier: str = "maxiops",
        attached_service_ids: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
    ) -> AppService:
        """Create a new app service.

        Args:
            name: Display name for the app.
            plan_name: Compute plan identifier (e.g. "tier-2").
            app_config: Container image and port configuration.
            zone: Deployment zone (e.g. "se-sto1").
            storage_size_gb: Size of the data disk in gigabytes (minimum 10).
            storage_tier: Storage performance tier ("standard" or "maxiops").
            attached_service_ids: Managed service IDs to attach at creation time.
            organization_id: Optional org ID for this request.
        """
        body: Dict[str, Any] = {
            "name": name,
            "plan_name": plan_name,
            "app_config": app_config.to_dict(),
            "storage_size_gb": storage_size_gb,
            "storage_tier": storage_tier,
        }
        if zone is not None:
            body["zone"] = zone
        if attached_service_ids:
            body["attached_service_ids"] = attached_service_ids
        if organization_id is not None:
            body["organization_id"] = organization_id
        extra_headers: Dict[str, str] = {}
        if organization_id:
            extra_headers["X-Active-Org-ID"] = organization_id
        data = await self._http.post("/app-services", body, extra_headers=extra_headers or None)
        return AppService.from_dict(data)

    async def get(self, app_service_id: str) -> AppService:
        """Get an app service by ID."""
        data = await self._http.get(f"/app-services/{app_service_id}")
        return AppService.from_dict(data)

    async def update(self, app_service_id: str, *, app_config: AppContainerConfig) -> AppService:
        """Update an app service's container configuration."""
        body: Dict[str, Any] = {"app_config": app_config.to_dict()}
        data = await self._http.patch(f"/app-services/{app_service_id}", body)
        return AppService.from_dict(data)

    async def delete(self, app_service_id: str) -> None:
        """Delete an app service."""
        await self._http.delete(f"/app-services/{app_service_id}")

    async def restart(self, app_service_id: str) -> None:
        """Restart the app's running container in place."""
        await self._http.post(f"/app-services/{app_service_id}/restart")

    async def scale(self, app_service_id: str, *, plan_name: str) -> AppService:
        """Change the app's compute plan."""
        body: Dict[str, Any] = {"plan_name": plan_name}
        data = await self._http.post(f"/app-services/{app_service_id}/scale", body)
        return AppService.from_dict(data)

    async def attach(self, app_service_id: str, *, attached_service_id: str) -> AppService:
        """Attach a managed service to a running app.

        The target may be a database or another app (east-west app-to-app).
        The platform peers the private networks, opens the target's port to the
        app's subnet, and rolls a zero-downtime redeploy so the injected
        environment is updated: a database injects connection credentials; an
        app injects ``MDB_<NAME>_HOST/PORT/URL`` for plain-HTTP calls over the
        private SDN (no credentials, no ``DATABASE_URL``). An app supports up
        to five attachments (databases and apps combined). The target must be
        Running, owned by the same user, in the app's peering region, and not
        the app itself.

        Args:
            app_service_id: ID of the app service to attach to.
            attached_service_id: ID of the database or app service to attach.
        """
        body: Dict[str, Any] = {"attached_service_id": attached_service_id}
        data = await self._http.post(f"/app-services/{app_service_id}/attachments", body)
        return AppService.from_dict(data)

    async def detach(self, app_service_id: str, attachment_id: str) -> AppService:
        """Remove an attachment from a running app."""
        data = await self._http.delete(f"/app-services/{app_service_id}/attachments/{attachment_id}")  # type: ignore[assignment]
        if data is None:
            return await self.get(app_service_id)
        return AppService.from_dict(data)

    # ------------------------------------------------------------------
    # Deployment history
    # ------------------------------------------------------------------

    async def list_deployments(self, app_service_id: str) -> List[AppDeployment]:
        """List the deploy history of an app service, newest first.

        Each entry is a previously rolled-out image and configuration.
        ``deploy_logs`` on each entry holds the ordered steps the agent
        executed for that revision (image start, health probe, ingress
        cutover, previous-color teardown).

        Args:
            app_service_id: ID of the app service.
        """
        data = await self._http.get(f"/app-services/{app_service_id}/deployments")
        return [AppDeployment.from_dict(d) for d in data.get("deployments", [])]

    async def rollback(self, app_service_id: str, *, deployment_id: str) -> AppService:
        """Redeploy an earlier revision via a zero-downtime blue/green swap.

        Args:
            app_service_id: ID of the app service.
            deployment_id: ID of the deployment to roll back to (from
                ``list_deployments``).
        """
        body: Dict[str, Any] = {"deployment_id": deployment_id}
        data = await self._http.post(f"/app-services/{app_service_id}/rollback", body)
        return AppService.from_dict(data)

    # ------------------------------------------------------------------
    # Auth methods
    # ------------------------------------------------------------------

    async def enable_app_service_auth(
        self, app_service_id: str, req: AuthEnableRequest
    ) -> AuthConfigurationWithKeys:
        """Enable end-user authentication for an app service.

        Provisions a managed OIDC identity provider backed by one of the app's
        attached PostgreSQL services. SMTP credentials in the request are stored
        in the platform secret store and never returned. To enable social login
        (Google or GitHub) populate ``req.idp_providers``; each provider's
        client secret is stored in the secret store and never returned.

        Args:
            app_service_id: ID of the app service to enable auth for.
            req: Auth enable parameters including SMTP credentials, optional
                branding theme, and optional social-login providers.

        Returns:
            The auth configuration and its signing key records.
        """
        data = await self._http.post(
            f"/app-services/{app_service_id}/auth/enable", req.to_dict()
        )
        return AuthConfigurationWithKeys.from_dict(data)

    async def get_app_service_auth(
        self, app_service_id: str
    ) -> Optional[AuthConfigurationWithKeys]:
        """Get the auth configuration for an app service.

        Returns ``None`` when auth is not enabled (404 from the API).

        Args:
            app_service_id: ID of the app service.

        Returns:
            The auth configuration and signing key records, or ``None`` if auth
            is not enabled.
        """
        try:
            data = await self._http.get(f"/app-services/{app_service_id}/auth")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return AuthConfigurationWithKeys.from_dict(data)

    async def disable_app_service_auth(self, app_service_id: str) -> str:
        """Disable end-user authentication for an app service.

        Args:
            app_service_id: ID of the app service.

        Returns:
            The new status string (``"Disabled"``).
        """
        data = await self._http.post(f"/app-services/{app_service_id}/auth/disable")
        return data.get("status", "Disabled") if data else "Disabled"

    async def rotate_app_service_auth_key(self, app_service_id: str) -> AuthSigningKey:
        """Rotate the JWT signing key for an app service's auth.

        Args:
            app_service_id: ID of the app service.

        Returns:
            The newly minted signing key record.
        """
        data = await self._http.post(
            f"/app-services/{app_service_id}/auth/rotate-key"
        )
        return AuthSigningKey.from_dict(data.get("signing_key", {}))

    async def revoke_app_service_auth_session(
        self, app_service_id: str, session_id: str
    ) -> str:
        """Revoke one end-user session.

        Args:
            app_service_id: ID of the app service.
            session_id: The end-user session id to revoke.

        Returns:
            The dispatched task id.
        """
        data = await self._http.post(
            f"/app-services/{app_service_id}/auth/sessions/{session_id}/revoke"
        )
        return data.get("task_id", "") if data else ""

    async def delete_app_service_auth_user(
        self,
        app_service_id: str,
        *,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Erase one end-user under the GDPR right to erasure (Art. 17).

        Exactly one of ``email`` or ``user_id`` must be supplied.

        Args:
            app_service_id: ID of the app service.
            email: Address the end-user by email. Mutually exclusive with
                ``user_id``.
            user_id: Address the end-user by their auth subject UUID. Mutually
                exclusive with ``email``.

        Returns:
            The dispatched task id for status polling.
        """
        if not email and not user_id:
            raise ValueError("Exactly one of email or user_id must be provided")
        body: Dict[str, Any] = {}
        if email:
            body["email"] = email
        if user_id:
            body["user_id"] = user_id
        data = await self._http.post(
            f"/app-services/{app_service_id}/auth/users/delete", body
        )
        return data.get("task_id", "") if data else ""

    async def delete_app_service_auth_user_by_identifier(
        self, app_service_id: str, identifier: str
    ) -> str:
        """Erase one end-user by identifier via DELETE
        /app-services/{id}/auth/users/{identifier}.

        Args:
            app_service_id: ID of the app service.
            identifier: The user identifier to erase.

        Returns:
            The dispatched task id for status polling.
        """
        data = await self._http.delete(
            f"/app-services/{app_service_id}/auth/users/{identifier}"
        )
        return data.get("task_id", "") if data else ""  # type: ignore[union-attr]

    async def list_auth_providers(self, app_service_id: str) -> List[IdpProviderConfig]:
        """List the social-login providers configured for an app service's auth.

        Returns the non-secret portion of each provider record. Client secrets
        are custodied in the platform secret store and are never returned.

        Args:
            app_service_id: ID of the app service.

        Returns:
            The list of configured social-login providers.
        """
        data = await self._http.get(f"/app-services/{app_service_id}/auth/providers")
        return [IdpProviderConfig.from_dict(p) for p in data.get("providers", [])]

    async def upsert_auth_provider(
        self,
        app_service_id: str,
        provider: str,
        *,
        client_id: str,
        client_secret: str,
        display_name: Optional[str] = None,
    ) -> List[IdpProviderConfig]:
        """Add or update a social-login provider for an app service's auth.

        The ``client_secret`` is write-only: it is stored in the platform
        secret store and never returned in any response.

        Args:
            app_service_id: ID of the app service.
            provider: Provider identifier (e.g. ``"google"`` or ``"github"``).
            client_id: OAuth2 client ID issued by the provider.
            client_secret: OAuth2 client secret issued by the provider. Stored
                in the secret store; never logged or returned.
            display_name: Optional human-readable label shown on the login UI.

        Returns:
            The updated list of all configured social-login providers.
        """
        body: Dict[str, Any] = {
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if display_name is not None:
            body["display_name"] = display_name
        data = await self._http.put(
            f"/app-services/{app_service_id}/auth/providers/{provider}", body
        )
        return [IdpProviderConfig.from_dict(p) for p in data.get("providers", [])]

    async def remove_auth_provider(
        self, app_service_id: str, provider: str
    ) -> List[IdpProviderConfig]:
        """Remove a social-login provider from an app service's auth.

        Args:
            app_service_id: ID of the app service.
            provider: Provider identifier to remove (e.g. ``"google"``).

        Returns:
            The remaining list of configured social-login providers.
        """
        data = await self._http.delete(
            f"/app-services/{app_service_id}/auth/providers/{provider}"
        )
        return [IdpProviderConfig.from_dict(p) for p in data.get("providers", [])]  # type: ignore[union-attr]
