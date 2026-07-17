"""
FoundryDB SDK - Managed inference LoRA adapter registry (sync and async).

Manages the customer LoRA fine-tuned adapter registry for managed inference
services: an open-weight LLM served by vLLM on a dedicated GPU server. A LoRA
adapter is a small set of fine-tuned weights, trained on the organization's own
data, that is hot-loaded onto the base model's GPU. The flow is two-step: the
fine-tuning workflow uploads the adapter artifact (``adapter_model.safetensors``
and ``adapter_config.json``) to the organization's Files bucket and calls
``register_adapter`` to record an ``uploaded``, promotable version, then
``promote_adapter`` downloads the weights, verifies their hash, and hot-loads
them into vLLM with no restart. Once active, the service answers to the adapter
as ``foundrydb_managed/<served_model_name>`` on the OpenAI-compatible endpoint.
An adapter never leaves its owning organization's boundary.

This is distinct from the inference proxy surface in ``inference.py``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HTTPClient, AsyncHTTPClient
from .types import InferenceModelAdapter


def _register_body(
    *,
    base_model_id: str,
    served_model_name: str,
    version: int,
    files_bucket: str,
    files_key_prefix: str,
    adapter_sha256: str,
    size_bytes: int,
    base_model_license: Optional[str],
    organization_id: Optional[str],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "base_model_id": base_model_id,
        "served_model_name": served_model_name,
        "version": version,
        "files_bucket": files_bucket,
        "files_key_prefix": files_key_prefix,
        "adapter_sha256": adapter_sha256,
        "size_bytes": size_bytes,
    }
    if base_model_license is not None:
        body["base_model_license"] = base_model_license
    if organization_id is not None:
        body["organization_id"] = organization_id
    return body


class InferenceServicesAPI:
    """Manages the managed inference LoRA adapter registry (sync)."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def register_adapter(
        self,
        *,
        base_model_id: str,
        served_model_name: str,
        version: int,
        files_bucket: str,
        files_key_prefix: str,
        adapter_sha256: str,
        size_bytes: int,
        base_model_license: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> InferenceModelAdapter:
        """Register an uploaded LoRA fine-tuned adapter version, making it promotable.

        Call it after uploading the adapter artifact to the organization's Files
        bucket; ``promote_adapter`` later binds the version to a GPU and
        hot-loads it. The row is org-scoped and unbound
        (``inference_service_id`` is ``None``) until promote, and it enters the
        registry with status ``uploaded``.

        Args:
            base_model_id: The base model the adapter was trained against; it
                must later match the serving service's model id or Hugging Face
                repo.
            served_model_name: Customer-facing name the adapter answers to,
                becoming ``foundrydb_managed/<served_model_name>``. Letters,
                digits, ``.``, ``_`` and ``-`` only, at most 128 characters.
            version: Monotonic version per (organization, served model name);
                must be at least 1.
            files_bucket: The organization's Files bucket holding the artifact.
            files_key_prefix: Files key prefix holding
                ``adapter_model.safetensors`` and ``adapter_config.json``.
            adapter_sha256: 64-char lowercase hex sha256 of
                ``adapter_model.safetensors``, re-verified after download.
            size_bytes: Artifact size in bytes; must not be negative.
            base_model_license: The base-model license that travels with the
                weights. Optional.
            organization_id: Register under a specific organization the caller
                belongs to (a platform admin may target any). Defaults to the
                caller's active organization.
        """
        body = _register_body(
            base_model_id=base_model_id,
            served_model_name=served_model_name,
            version=version,
            files_bucket=files_bucket,
            files_key_prefix=files_key_prefix,
            adapter_sha256=adapter_sha256,
            size_bytes=size_bytes,
            base_model_license=base_model_license,
            organization_id=organization_id,
        )
        extra_headers: Dict[str, str] = {}
        if organization_id:
            extra_headers["X-Active-Org-ID"] = organization_id
        data = self._http.post(
            "/inference-services/adapters", body, extra_headers=extra_headers or None
        )
        return InferenceModelAdapter.from_dict(data.get("adapter", data))

    def list_adapters(self, service_id: str) -> List[InferenceModelAdapter]:
        """List the LoRA fine-tuned adapter versions relevant to the service.

        Returns, newest first, the versions bound to the service (the currently
        active version plus its superseded history) together with the
        organization's uploaded, not-yet-promoted versions trained on this
        service's base model, so a freshly registered adapter can be promoted
        from here. An uploaded version carries status ``uploaded`` with a
        ``None`` ``inference_service_id`` until it is promoted; uploaded versions
        for another base model, organization, or service are not listed. Returns
        an empty list when nothing is bound or promotable.
        """
        data = self._http.get(f"/inference-services/{service_id}/adapters")
        return [
            InferenceModelAdapter.from_dict(a) for a in (data or {}).get("adapters", [])
        ]

    def promote_adapter(
        self, service_id: str, adapter_id: str
    ) -> InferenceModelAdapter:
        """Promote a LoRA fine-tuned adapter version onto the service's serving GPU.

        The platform downloads the adapter weights from Files, verifies their
        hash, and hot-loads them into vLLM with no restart. The promoted version
        becomes ``active`` and any previously active version is marked
        ``superseded``. Rollback is achieved through this same method by
        promoting a prior (superseded) version, so one call covers both
        directions. Requires manage-level authority; the request has no body.
        """
        data = self._http.post(
            f"/inference-services/{service_id}/adapters/{adapter_id}/promote"
        )
        return InferenceModelAdapter.from_dict((data or {}).get("adapter", data))


class AsyncInferenceServicesAPI:
    """Manages the managed inference LoRA adapter registry (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def register_adapter(
        self,
        *,
        base_model_id: str,
        served_model_name: str,
        version: int,
        files_bucket: str,
        files_key_prefix: str,
        adapter_sha256: str,
        size_bytes: int,
        base_model_license: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> InferenceModelAdapter:
        """Register an uploaded LoRA fine-tuned adapter version, making it promotable.

        See :meth:`InferenceServicesAPI.register_adapter`.
        """
        body = _register_body(
            base_model_id=base_model_id,
            served_model_name=served_model_name,
            version=version,
            files_bucket=files_bucket,
            files_key_prefix=files_key_prefix,
            adapter_sha256=adapter_sha256,
            size_bytes=size_bytes,
            base_model_license=base_model_license,
            organization_id=organization_id,
        )
        extra_headers: Dict[str, str] = {}
        if organization_id:
            extra_headers["X-Active-Org-ID"] = organization_id
        data = await self._http.post(
            "/inference-services/adapters", body, extra_headers=extra_headers or None
        )
        return InferenceModelAdapter.from_dict(data.get("adapter", data))

    async def list_adapters(self, service_id: str) -> List[InferenceModelAdapter]:
        """List the LoRA fine-tuned adapter versions relevant to the service.

        Returns the bound versions (active plus superseded history) together
        with the organization's uploaded, not-yet-promoted versions trained on
        this service's base model. See
        :meth:`InferenceServicesAPI.list_adapters`.
        """
        data = await self._http.get(f"/inference-services/{service_id}/adapters")
        return [
            InferenceModelAdapter.from_dict(a) for a in (data or {}).get("adapters", [])
        ]

    async def promote_adapter(
        self, service_id: str, adapter_id: str
    ) -> InferenceModelAdapter:
        """Promote a LoRA fine-tuned adapter version onto the service's serving GPU.

        See :meth:`InferenceServicesAPI.promote_adapter`.
        """
        data = await self._http.post(
            f"/inference-services/{service_id}/adapters/{adapter_id}/promote"
        )
        return InferenceModelAdapter.from_dict((data or {}).get("adapter", data))
