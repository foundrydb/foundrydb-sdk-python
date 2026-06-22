"""
FoundryDB SDK - Compliance Evidence Packet API (sync and async).

Provides access to the platform's compliance reporting surface, covering
SOC 2 Type II and GDPR Article 30 Records of Processing Activities (ROPA).
Each report is a signed JSON evidence packet that can be fetched as
structured data or as a rendered PDF. The public signing-key endpoint
allows offline signature verification without platform credentials.
"""
from __future__ import annotations

from typing import List

from .client import AsyncHTTPClient, HTTPClient
from .types import (
    CompliancePacketResponse,
    ComplianceReportRecord,
    ComplianceSigningKeySet,
    ComplianceSubscription,
    GenerateComplianceReportResponse,
)


class ComplianceAPI:
    """Compliance evidence packet surface (sync).

    Methods on this class cover the full lifecycle of signed compliance
    reports: generation, listing, JSON download, PDF download, and public
    key discovery for offline signature verification.
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def generate_compliance_report(
        self,
        org_id: str,
        framework: str,
    ) -> GenerateComplianceReportResponse:
        """Generate a signed compliance evidence packet for an organization.

        The packet is persisted server-side and can be retrieved later via
        :meth:`download_compliance_report_json` or
        :meth:`download_compliance_report_pdf`.

        Args:
            org_id: UUID of the organization.
            framework: Compliance framework to evaluate. One of
                ``"soc2"`` or ``"gdpr_ropa"``.

        Returns:
            A :class:`~foundrydb.types.GenerateComplianceReportResponse`
            containing the new ``report_id``, the full evidence packet, and
            the detached signature.
        """
        data = self._http.post(
            f"/organizations/{org_id}/compliance-reports",
            {"framework": framework},
        )
        return GenerateComplianceReportResponse.from_dict(data)

    def list_compliance_reports(self, org_id: str) -> List[ComplianceReportRecord]:
        """List all compliance reports generated for an organization.

        Returns the index records in reverse-chronological order. Each record
        contains the framework, period, signing key metadata, and a
        ``has_pdf`` flag indicating whether a rendered PDF is available.

        Args:
            org_id: UUID of the organization.
        """
        data = self._http.get(f"/organizations/{org_id}/compliance-reports")
        return [ComplianceReportRecord.from_dict(r) for r in data.get("reports", [])]

    def download_compliance_report_json(
        self,
        org_id: str,
        report_id: str,
    ) -> CompliancePacketResponse:
        """Fetch a compliance report's signed evidence packet as structured data.

        Args:
            org_id: UUID of the organization.
            report_id: UUID of the report returned by
                :meth:`generate_compliance_report` or
                :meth:`list_compliance_reports`.

        Returns:
            A :class:`~foundrydb.types.CompliancePacketResponse` containing
            the evidence packet and its detached signature.
        """
        data = self._http.get(
            f"/organizations/{org_id}/compliance-reports/{report_id}",
        )
        return CompliancePacketResponse.from_dict(data)

    def download_compliance_report_pdf(
        self,
        org_id: str,
        report_id: str,
    ) -> bytes:
        """Download a compliance report as a rendered PDF.

        Args:
            org_id: UUID of the organization.
            report_id: UUID of the report.

        Returns:
            Raw PDF bytes. Write these directly to a file:

            .. code-block:: python

                pdf = client.compliance.download_compliance_report_pdf(
                    org_id, report_id
                )
                with open("report.pdf", "wb") as f:
                    f.write(pdf)
        """
        return self._http.get_raw(
            f"/organizations/{org_id}/compliance-reports/{report_id}/pdf",
        )

    def compliance_signing_keys(self) -> ComplianceSigningKeySet:
        """Return the platform's public compliance signing keys.

        This endpoint is unauthenticated and is intended for offline
        signature verification of compliance packets. The response lists
        all active (and recently retired) signing keys.

        Returns:
            A :class:`~foundrydb.types.ComplianceSigningKeySet` with the
            algorithm and the list of public keys.
        """
        data = self._http.get("/.well-known/compliance-signing-keys")
        return ComplianceSigningKeySet.from_dict(data)

    def list_compliance_subscriptions(self, org_id: str) -> List[ComplianceSubscription]:
        """List compliance framework subscriptions for an organization.

        Returns all subscriptions, including those that have been canceled.
        Each entry reflects the current billing state of one framework.

        Args:
            org_id: UUID of the organization.
        """
        data = self._http.get(f"/organizations/{org_id}/compliance-subscriptions")
        return [ComplianceSubscription.from_dict(s) for s in data.get("subscriptions", [])]

    def subscribe_compliance_framework(
        self,
        org_id: str,
        framework: str,
    ) -> ComplianceSubscription:
        """Subscribe an organization to a compliance framework.

        Idempotent: re-subscribing an already-active subscription is a no-op
        and returns the current subscription record.

        Args:
            org_id: UUID of the organization.
            framework: Compliance framework identifier. One of ``"soc2"``,
                ``"gdpr_ropa"``, ``"dora"``, or ``"eu_ai_act"``.

        Returns:
            The resulting :class:`~foundrydb.types.ComplianceSubscription`.
        """
        data = self._http.put(
            f"/organizations/{org_id}/compliance-subscriptions/{framework}",
            {},
        )
        return ComplianceSubscription.from_dict(data)

    def unsubscribe_compliance_framework(self, org_id: str, framework: str) -> None:
        """Cancel a compliance framework subscription for an organization.

        The subscription record is retained with its ``canceled_at`` timestamp
        set. Unsubscribing stops future billing for that framework.

        Args:
            org_id: UUID of the organization.
            framework: Compliance framework identifier to cancel.
        """
        self._http.delete(
            f"/organizations/{org_id}/compliance-subscriptions/{framework}",
        )

    def rotate_compliance_signing_key(self) -> ComplianceSigningKeySet:
        """Rotate the platform compliance signing key (admin only).

        Generates a new Ed25519 keypair, makes it the active signing key, and
        retires the previous key. The retired key remains in the key set for
        offline verification of packets signed before the rotation.

        Returns:
            The updated :class:`~foundrydb.types.ComplianceSigningKeySet`
            reflecting the new active key and all retired keys.
        """
        data = self._http.post("/admin/compliance/signing-keys/rotate", {})
        return ComplianceSigningKeySet.from_dict(data)


class AsyncComplianceAPI:
    """Compliance evidence packet surface (async)."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def generate_compliance_report(
        self,
        org_id: str,
        framework: str,
    ) -> GenerateComplianceReportResponse:
        """Generate a signed compliance evidence packet for an organization.

        Args:
            org_id: UUID of the organization.
            framework: ``"soc2"`` or ``"gdpr_ropa"``.
        """
        data = await self._http.post(
            f"/organizations/{org_id}/compliance-reports",
            {"framework": framework},
        )
        return GenerateComplianceReportResponse.from_dict(data)

    async def list_compliance_reports(self, org_id: str) -> List[ComplianceReportRecord]:
        """List all compliance reports generated for an organization.

        Args:
            org_id: UUID of the organization.
        """
        data = await self._http.get(f"/organizations/{org_id}/compliance-reports")
        return [ComplianceReportRecord.from_dict(r) for r in data.get("reports", [])]

    async def download_compliance_report_json(
        self,
        org_id: str,
        report_id: str,
    ) -> CompliancePacketResponse:
        """Fetch a compliance report's signed evidence packet as structured data.

        Args:
            org_id: UUID of the organization.
            report_id: UUID of the report.
        """
        data = await self._http.get(
            f"/organizations/{org_id}/compliance-reports/{report_id}",
        )
        return CompliancePacketResponse.from_dict(data)

    async def download_compliance_report_pdf(
        self,
        org_id: str,
        report_id: str,
    ) -> bytes:
        """Download a compliance report as a rendered PDF.

        Args:
            org_id: UUID of the organization.
            report_id: UUID of the report.

        Returns:
            Raw PDF bytes.
        """
        return await self._http.get_raw(
            f"/organizations/{org_id}/compliance-reports/{report_id}/pdf",
        )

    async def compliance_signing_keys(self) -> ComplianceSigningKeySet:
        """Return the platform's public compliance signing keys (unauthenticated).

        Returns:
            A :class:`~foundrydb.types.ComplianceSigningKeySet` with the
            algorithm and list of public keys.
        """
        data = await self._http.get("/.well-known/compliance-signing-keys")
        return ComplianceSigningKeySet.from_dict(data)

    async def list_compliance_subscriptions(self, org_id: str) -> List[ComplianceSubscription]:
        """List compliance framework subscriptions for an organization.

        Args:
            org_id: UUID of the organization.
        """
        data = await self._http.get(f"/organizations/{org_id}/compliance-subscriptions")
        return [ComplianceSubscription.from_dict(s) for s in data.get("subscriptions", [])]

    async def subscribe_compliance_framework(
        self,
        org_id: str,
        framework: str,
    ) -> ComplianceSubscription:
        """Subscribe an organization to a compliance framework.

        Args:
            org_id: UUID of the organization.
            framework: Compliance framework identifier. One of ``"soc2"``,
                ``"gdpr_ropa"``, ``"dora"``, or ``"eu_ai_act"``.

        Returns:
            The resulting :class:`~foundrydb.types.ComplianceSubscription`.
        """
        data = await self._http.put(
            f"/organizations/{org_id}/compliance-subscriptions/{framework}",
            {},
        )
        return ComplianceSubscription.from_dict(data)

    async def unsubscribe_compliance_framework(self, org_id: str, framework: str) -> None:
        """Cancel a compliance framework subscription for an organization.

        Args:
            org_id: UUID of the organization.
            framework: Compliance framework identifier to cancel.
        """
        await self._http.delete(
            f"/organizations/{org_id}/compliance-subscriptions/{framework}",
        )

    async def rotate_compliance_signing_key(self) -> ComplianceSigningKeySet:
        """Rotate the platform compliance signing key (admin only).

        Generates a new Ed25519 keypair, makes it the active signing key, and
        retires the previous key. The retired key remains in the key set for
        offline verification of packets signed before the rotation.

        Returns:
            The updated :class:`~foundrydb.types.ComplianceSigningKeySet`
            reflecting the new active key and all retired keys.
        """
        data = await self._http.post("/admin/compliance/signing-keys/rotate", {})
        return ComplianceSigningKeySet.from_dict(data)
