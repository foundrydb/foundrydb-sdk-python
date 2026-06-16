"""
FoundryDB SDK - Inference Proxy API (sync and async).

Organizations bring their own provider API keys, mint dedicated data-plane
keys for their applications, set org-wide policy (EU-only routing, monthly
cost circuit breaker), and read aggregated usage. The data plane itself is
OpenAI-compatible at /inference/v1/* authenticated with fdb-inf keys.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import (
    InferenceProviderConfig,
    InferenceKey,
    CreateInferenceKeyResult,
    OrgInferenceSettings,
    InferenceUsageSummary,
)


class InferenceAPI:
    """Manages the inference proxy for an organization (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    @staticmethod
    def _base(org_id: str) -> str:
        return f"/organizations/{org_id}/inference"

    # ------------------------------------------------------------------
    # Provider configuration
    # ------------------------------------------------------------------

    def list_providers(self, org_id: str) -> List[InferenceProviderConfig]:
        """Return the organization's configured AI providers."""
        data = self._http.get(f"{self._base(org_id)}/providers")
        return [InferenceProviderConfig.from_dict(p) for p in data.get("providers", [])]

    def upsert_provider(
        self,
        org_id: str,
        *,
        provider: str,
        api_key: str,
        eu_endpoint: bool = False,
        enabled: Optional[bool] = None,
        base_url: Optional[str] = None,
    ) -> InferenceProviderConfig:
        """Create or replace the organization's config for one provider.

        ``api_key`` is required on first configuration; on update an empty
        ``api_key`` keeps the stored one. ``provider`` is one of
        ``openai``, ``anthropic``, ``mistral``, ``azure_openai``. Azure
        OpenAI requires ``base_url`` (the Azure resource endpoint).

        Args:
            org_id: Organization ID.
            provider: Provider identifier.
            api_key: Provider API key.
            eu_endpoint: Route requests through the provider's EU endpoint.
            enabled: Whether the provider is active. Defaults to True.
            base_url: Custom endpoint URL (required for azure_openai).
        """
        body: Dict[str, Any] = {
            "provider": provider,
            "api_key": api_key,
            "eu_endpoint": eu_endpoint,
        }
        if enabled is not None:
            body["enabled"] = enabled
        if base_url is not None:
            body["base_url"] = base_url
        data = self._http.put(f"{self._base(org_id)}/providers", body)
        return InferenceProviderConfig.from_dict(data)

    def delete_provider(self, org_id: str, provider: str) -> None:
        """Remove the organization's config for one provider."""
        self._http.delete(f"{self._base(org_id)}/providers/{provider}")

    # ------------------------------------------------------------------
    # Data-plane keys
    # ------------------------------------------------------------------

    def list_keys(self, org_id: str) -> List[InferenceKey]:
        """Return the organization's data-plane keys (no secrets)."""
        data = self._http.get(f"{self._base(org_id)}/keys")
        return [InferenceKey.from_dict(k) for k in data.get("keys", [])]

    def create_key(
        self,
        org_id: str,
        *,
        name: str,
        monthly_token_limit: int,
        rate_limit_rpm: Optional[int] = None,
    ) -> CreateInferenceKeyResult:
        """Mint a new data-plane key.

        The returned secret is shown exactly once; store it immediately.
        ``monthly_token_limit`` is required and must be positive.

        Args:
            org_id: Organization ID.
            name: Human-readable label for the key.
            monthly_token_limit: Per-month token ceiling (required, > 0).
            rate_limit_rpm: Requests-per-minute cap. Defaults to unlimited.
        """
        body: Dict[str, Any] = {
            "name": name,
            "monthly_token_limit": monthly_token_limit,
        }
        if rate_limit_rpm is not None:
            body["rate_limit_rpm"] = rate_limit_rpm
        data = self._http.post(f"{self._base(org_id)}/keys", body)
        return CreateInferenceKeyResult.from_dict(data)

    def revoke_key(self, org_id: str, key_id: str) -> None:
        """Revoke a data-plane key. Revocation is immediate and irreversible."""
        self._http.delete(f"{self._base(org_id)}/keys/{key_id}")

    # ------------------------------------------------------------------
    # Org-wide settings
    # ------------------------------------------------------------------

    def get_settings(self, org_id: str) -> Optional[OrgInferenceSettings]:
        """Return the organization's proxy policy settings.

        Returns ``None`` when settings have not been configured yet (404).
        """
        try:
            data = self._http.get(f"{self._base(org_id)}/settings")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return OrgInferenceSettings.from_dict(data)

    def update_settings(
        self,
        org_id: str,
        *,
        eu_only: Optional[bool] = None,
        monthly_cost_limit_cents: Optional[int] = None,
        reset_circuit: bool = False,
    ) -> OrgInferenceSettings:
        """Update org-wide proxy policy settings.

        ``monthly_cost_limit_cents`` is required when configuring settings for
        the first time. ``reset_circuit=True`` closes an open cost circuit.

        Args:
            org_id: Organization ID.
            eu_only: Route all requests through EU-resident endpoints only.
            monthly_cost_limit_cents: Monthly cost ceiling in microcents.
            reset_circuit: Close an open monthly-cost circuit breaker.
        """
        body: Dict[str, Any] = {}
        if eu_only is not None:
            body["eu_only"] = eu_only
        if monthly_cost_limit_cents is not None:
            body["monthly_cost_limit_cents"] = monthly_cost_limit_cents
        if reset_circuit:
            body["reset_circuit"] = True
        data = self._http.put(f"{self._base(org_id)}/settings", body)
        return OrgInferenceSettings.from_dict(data)

    # ------------------------------------------------------------------
    # Usage
    # ------------------------------------------------------------------

    def get_usage(
        self,
        org_id: str,
        *,
        from_: str = "",
        to: str = "",
        group_by: str = "",
    ) -> InferenceUsageSummary:
        """Return aggregated inference usage for the organization.

        Args:
            org_id: Organization ID.
            from_: RFC 3339 start timestamp. Defaults to the start of the
                current month.
            to: RFC 3339 end timestamp. Defaults to now.
            group_by: ``"model"`` or ``"key"``. Defaults to ``"model"``.
        """
        params: Dict[str, Any] = {}
        if from_:
            params["from"] = from_
        if to:
            params["to"] = to
        if group_by:
            params["group_by"] = group_by
        data = self._http.get(
            f"{self._base(org_id)}/usage",
            params=params or None,
        )
        return InferenceUsageSummary.from_dict(data)


class AsyncInferenceAPI:
    """Manages the inference proxy for an organization (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    @staticmethod
    def _base(org_id: str) -> str:
        return f"/organizations/{org_id}/inference"

    async def list_providers(self, org_id: str) -> List[InferenceProviderConfig]:
        """Return the organization's configured AI providers."""
        data = await self._http.get(f"{self._base(org_id)}/providers")
        return [InferenceProviderConfig.from_dict(p) for p in data.get("providers", [])]

    async def upsert_provider(
        self,
        org_id: str,
        *,
        provider: str,
        api_key: str,
        eu_endpoint: bool = False,
        enabled: Optional[bool] = None,
        base_url: Optional[str] = None,
    ) -> InferenceProviderConfig:
        """Create or replace the organization's config for one provider."""
        body: Dict[str, Any] = {
            "provider": provider,
            "api_key": api_key,
            "eu_endpoint": eu_endpoint,
        }
        if enabled is not None:
            body["enabled"] = enabled
        if base_url is not None:
            body["base_url"] = base_url
        data = await self._http.put(f"{self._base(org_id)}/providers", body)
        return InferenceProviderConfig.from_dict(data)

    async def delete_provider(self, org_id: str, provider: str) -> None:
        """Remove the organization's config for one provider."""
        await self._http.delete(f"{self._base(org_id)}/providers/{provider}")

    async def list_keys(self, org_id: str) -> List[InferenceKey]:
        """Return the organization's data-plane keys (no secrets)."""
        data = await self._http.get(f"{self._base(org_id)}/keys")
        return [InferenceKey.from_dict(k) for k in data.get("keys", [])]

    async def create_key(
        self,
        org_id: str,
        *,
        name: str,
        monthly_token_limit: int,
        rate_limit_rpm: Optional[int] = None,
    ) -> CreateInferenceKeyResult:
        """Mint a new data-plane key. The secret is shown exactly once."""
        body: Dict[str, Any] = {
            "name": name,
            "monthly_token_limit": monthly_token_limit,
        }
        if rate_limit_rpm is not None:
            body["rate_limit_rpm"] = rate_limit_rpm
        data = await self._http.post(f"{self._base(org_id)}/keys", body)
        return CreateInferenceKeyResult.from_dict(data)

    async def revoke_key(self, org_id: str, key_id: str) -> None:
        """Revoke a data-plane key."""
        await self._http.delete(f"{self._base(org_id)}/keys/{key_id}")

    async def get_settings(self, org_id: str) -> Optional[OrgInferenceSettings]:
        """Return the organization's proxy policy settings."""
        try:
            data = await self._http.get(f"{self._base(org_id)}/settings")
        except Exception as exc:
            from .types import FoundryDBError
            if isinstance(exc, FoundryDBError) and exc.status_code == 404:
                return None
            raise
        return OrgInferenceSettings.from_dict(data)

    async def update_settings(
        self,
        org_id: str,
        *,
        eu_only: Optional[bool] = None,
        monthly_cost_limit_cents: Optional[int] = None,
        reset_circuit: bool = False,
    ) -> OrgInferenceSettings:
        """Update org-wide proxy policy settings."""
        body: Dict[str, Any] = {}
        if eu_only is not None:
            body["eu_only"] = eu_only
        if monthly_cost_limit_cents is not None:
            body["monthly_cost_limit_cents"] = monthly_cost_limit_cents
        if reset_circuit:
            body["reset_circuit"] = True
        data = await self._http.put(f"{self._base(org_id)}/settings", body)
        return OrgInferenceSettings.from_dict(data)

    async def get_usage(
        self,
        org_id: str,
        *,
        from_: str = "",
        to: str = "",
        group_by: str = "",
    ) -> InferenceUsageSummary:
        """Return aggregated inference usage for the organization."""
        params: Dict[str, Any] = {}
        if from_:
            params["from"] = from_
        if to:
            params["to"] = to
        if group_by:
            params["group_by"] = group_by
        data = await self._http.get(
            f"{self._base(org_id)}/usage",
            params=params or None,
        )
        return InferenceUsageSummary.from_dict(data)
