"""
Tests for foundrydb.organizations - OrganizationsAPI (sync) and AsyncOrganizationsAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.organizations import OrganizationsAPI, AsyncOrganizationsAPI
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import Organization, FoundryDBError

BASE = "https://api.foundrydb.test"

ORG_PAYLOAD = {
    "id": "org-001",
    "name": "My Org",
    "slug": "my-org",
    "is_personal": False,
}

PERSONAL_ORG_PAYLOAD = {
    "id": "org-personal",
    "name": "Personal",
    "slug": "personal",
    "is_personal": True,
}


def make_sync_api() -> OrganizationsAPI:
    return OrganizationsAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncOrganizationsAPI:
    return AsyncOrganizationsAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Sync OrganizationsAPI
# ---------------------------------------------------------------------------

class TestOrganizationsAPISync:
    @respx.mock
    def test_list_returns_organization_objects(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": [ORG_PAYLOAD, PERSONAL_ORG_PAYLOAD]})
        )
        api = make_sync_api()
        orgs = api.list()
        assert len(orgs) == 2
        assert all(isinstance(o, Organization) for o in orgs)

    @respx.mock
    def test_list_org_fields(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": [ORG_PAYLOAD]})
        )
        api = make_sync_api()
        org = api.list()[0]
        assert org.id == "org-001"
        assert org.name == "My Org"
        assert org.slug == "my-org"
        assert org.is_personal is False

    @respx.mock
    def test_list_personal_org(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": [PERSONAL_ORG_PAYLOAD]})
        )
        api = make_sync_api()
        org = api.list()[0]
        assert org.is_personal is True

    @respx.mock
    def test_list_empty(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": []})
        )
        api = make_sync_api()
        assert api.list() == []

    @respx.mock
    def test_list_handles_list_response(self):
        """API may return a plain list instead of a dict."""
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json=[ORG_PAYLOAD])
        )
        api = make_sync_api()
        orgs = api.list()
        assert len(orgs) == 1
        assert orgs[0].id == "org-001"

    @respx.mock
    def test_list_raises_on_401(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.list()
        assert exc_info.value.status_code == 401

    @respx.mock
    def test_list_raises_on_500(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.list()
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_raw_field_populated(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": [ORG_PAYLOAD]})
        )
        api = make_sync_api()
        org = api.list()[0]
        assert org.raw == ORG_PAYLOAD


# ---------------------------------------------------------------------------
# Async AsyncOrganizationsAPI
# ---------------------------------------------------------------------------

class TestAsyncOrganizationsAPI:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_returns_organization_objects(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": [ORG_PAYLOAD, PERSONAL_ORG_PAYLOAD]})
        )
        api = make_async_api()
        orgs = await api.list()
        assert len(orgs) == 2
        assert all(isinstance(o, Organization) for o in orgs)
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_org_fields(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": [ORG_PAYLOAD]})
        )
        api = make_async_api()
        org = (await api.list())[0]
        assert org.id == "org-001"
        assert org.name == "My Org"
        assert org.slug == "my-org"
        assert org.is_personal is False
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_empty(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json={"organizations": []})
        )
        api = make_async_api()
        assert await api.list() == []
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_handles_list_response(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(200, json=[ORG_PAYLOAD])
        )
        api = make_async_api()
        orgs = await api.list()
        assert len(orgs) == 1
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_401(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError) as exc_info:
            await api.list()
        assert exc_info.value.status_code == 401
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_500(self):
        respx.get(f"{BASE}/organizations/").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.list()
        await api._http.aclose()
