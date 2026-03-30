"""
Tests for foundrydb.client - HTTPClient, AsyncHTTPClient, FoundryDB, AsyncFoundryDB.

Uses respx to mock httpx transports (works for both sync and async httpx clients).
"""
from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx

from foundrydb.client import (
    HTTPClient,
    AsyncHTTPClient,
    FoundryDB,
    AsyncFoundryDB,
    _build_auth_header,
    _raise_for_status,
)
from foundrydb.types import FoundryDBError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = "https://api.foundrydb.test"


def _make_sync_client(**kwargs) -> HTTPClient:
    return HTTPClient(BASE, "admin", "admin", **kwargs)


def _make_async_client(**kwargs) -> AsyncHTTPClient:
    return AsyncHTTPClient(BASE, "admin", "admin", **kwargs)


# ---------------------------------------------------------------------------
# _build_auth_header
# ---------------------------------------------------------------------------

class TestBuildAuthHeader:
    def test_produces_basic_token(self):
        header = _build_auth_header("user", "pass")
        expected = "Basic " + base64.b64encode(b"user:pass").decode()
        assert header == expected

    def test_special_characters_in_credentials(self):
        header = _build_auth_header("u@example.com", "p@ss:word!")
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode()
        assert decoded == "u@example.com:p@ss:word!"


# ---------------------------------------------------------------------------
# _raise_for_status
# ---------------------------------------------------------------------------

class TestRaiseForStatus:
    def _make_response(self, status: int, body: bytes = b"", content_type: str = "application/json"):
        request = httpx.Request("GET", "https://example.com")
        return httpx.Response(status, content=body, request=request,
                              headers={"content-type": content_type})

    def test_success_does_not_raise(self):
        resp = self._make_response(200, b'{"ok": true}')
        _raise_for_status(resp)  # should not raise

    def test_raises_foundrydb_error_on_4xx(self):
        body = json.dumps({"error": "not found"}).encode()
        resp = self._make_response(404, body)
        with pytest.raises(FoundryDBError) as exc_info:
            _raise_for_status(resp)
        err = exc_info.value
        assert err.status_code == 404
        assert "not found" in str(err)

    def test_raises_foundrydb_error_on_5xx(self):
        body = json.dumps({"message": "internal error"}).encode()
        resp = self._make_response(500, body)
        with pytest.raises(FoundryDBError) as exc_info:
            _raise_for_status(resp)
        err = exc_info.value
        assert err.status_code == 500
        assert "internal error" in str(err)

    def test_falls_back_to_http_status_when_body_unparseable(self):
        resp = self._make_response(503, b"not json", content_type="text/plain")
        with pytest.raises(FoundryDBError) as exc_info:
            _raise_for_status(resp)
        assert "503" in str(exc_info.value)

    def test_error_body_stored_on_exception(self):
        body = json.dumps({"error": "forbidden", "detail": "bad token"}).encode()
        resp = self._make_response(403, body)
        with pytest.raises(FoundryDBError) as exc_info:
            _raise_for_status(resp)
        assert exc_info.value.body["detail"] == "bad token"

    def test_repr_contains_status_code_and_message(self):
        body = json.dumps({"error": "oops"}).encode()
        resp = self._make_response(400, body)
        with pytest.raises(FoundryDBError) as exc_info:
            _raise_for_status(resp)
        r = repr(exc_info.value)
        assert "400" in r
        assert "oops" in r


# ---------------------------------------------------------------------------
# HTTPClient (sync)
# ---------------------------------------------------------------------------

class TestHTTPClientInternals:
    def test_url_method_returns_absolute_path_unchanged(self):
        client = _make_sync_client()
        # The _url helper is a passthrough in both branches.
        assert client._url("https://other.example.com/foo") == "https://other.example.com/foo"
        assert client._url("/relative/path") == "/relative/path"
        client.close()


class TestHTTPClientSync:
    @respx.mock
    def test_get_returns_parsed_json(self):
        respx.get(f"{BASE}/foo").mock(return_value=httpx.Response(200, json={"k": "v"}))
        client = _make_sync_client()
        result = client.get("/foo")
        assert result == {"k": "v"}

    @respx.mock
    def test_get_with_params(self):
        route = respx.get(f"{BASE}/foo").mock(return_value=httpx.Response(200, json={}))
        client = _make_sync_client()
        client.get("/foo", params={"a": "1"})
        assert route.called

    @respx.mock
    def test_get_empty_response_returns_none(self):
        respx.get(f"{BASE}/empty").mock(return_value=httpx.Response(200, content=b""))
        client = _make_sync_client()
        result = client.get("/empty")
        assert result is None

    @respx.mock
    def test_post_with_body(self):
        route = respx.post(f"{BASE}/things").mock(return_value=httpx.Response(201, json={"id": "1"}))
        client = _make_sync_client()
        result = client.post("/things", body={"name": "test"})
        assert result == {"id": "1"}
        assert route.called

    @respx.mock
    def test_post_without_body(self):
        respx.post(f"{BASE}/actions").mock(return_value=httpx.Response(200, json={"ok": True}))
        client = _make_sync_client()
        result = client.post("/actions")
        assert result == {"ok": True}

    @respx.mock
    def test_post_with_extra_headers(self):
        route = respx.post(f"{BASE}/org").mock(return_value=httpx.Response(200, json={}))
        client = _make_sync_client()
        client.post("/org", body={}, extra_headers={"X-Active-Org-ID": "org_123"})
        assert route.called

    @respx.mock
    def test_post_empty_response_returns_none(self):
        respx.post(f"{BASE}/noop").mock(return_value=httpx.Response(204, content=b""))
        client = _make_sync_client()
        result = client.post("/noop")
        assert result is None

    @respx.mock
    def test_patch_returns_parsed_json(self):
        respx.patch(f"{BASE}/items/1").mock(return_value=httpx.Response(200, json={"updated": True}))
        client = _make_sync_client()
        result = client.patch("/items/1", {"x": 1})
        assert result == {"updated": True}

    @respx.mock
    def test_delete_succeeds_with_no_return(self):
        respx.delete(f"{BASE}/items/1").mock(return_value=httpx.Response(204, content=b""))
        client = _make_sync_client()
        result = client.delete("/items/1")
        assert result is None

    @respx.mock
    def test_authorization_header_sent(self):
        route = respx.get(f"{BASE}/check").mock(return_value=httpx.Response(200, json={}))
        client = _make_sync_client()
        client.get("/check")
        sent_headers = route.calls.last.request.headers
        expected = _build_auth_header("admin", "admin")
        assert sent_headers.get("authorization") == expected

    @respx.mock
    def test_organization_id_sent_as_header(self):
        route = respx.get(f"{BASE}/check").mock(return_value=httpx.Response(200, json={}))
        client = HTTPClient(BASE, "admin", "admin", organization_id="org_xyz")
        client.get("/check")
        sent_headers = route.calls.last.request.headers
        assert sent_headers.get("x-active-org-id") == "org_xyz"

    @respx.mock
    def test_no_org_header_when_not_set(self):
        route = respx.get(f"{BASE}/check").mock(return_value=httpx.Response(200, json={}))
        client = _make_sync_client()
        client.get("/check")
        sent_headers = route.calls.last.request.headers
        assert "x-active-org-id" not in sent_headers

    @respx.mock
    def test_raises_on_error_status(self):
        respx.get(f"{BASE}/err").mock(return_value=httpx.Response(500, json={"error": "boom"}))
        client = _make_sync_client()
        with pytest.raises(FoundryDBError) as exc_info:
            client.get("/err")
        assert exc_info.value.status_code == 500

    def test_close_and_context_manager(self):
        with _make_sync_client() as client:
            assert isinstance(client, HTTPClient)
        # If close() is idempotent, no error here

    @respx.mock
    def test_base_url_trailing_slash_stripped(self):
        route = respx.get("https://api.foundrydb.test/path").mock(
            return_value=httpx.Response(200, json={})
        )
        client = HTTPClient("https://api.foundrydb.test/", "admin", "admin")
        client.get("/path")
        assert route.called


# ---------------------------------------------------------------------------
# AsyncHTTPClient
# ---------------------------------------------------------------------------

class TestAsyncHTTPClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self):
        respx.get(f"{BASE}/foo").mock(return_value=httpx.Response(200, json={"k": "v"}))
        client = _make_async_client()
        result = await client.get("/foo")
        assert result == {"k": "v"}
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_with_params(self):
        route = respx.get(f"{BASE}/foo").mock(return_value=httpx.Response(200, json={}))
        client = _make_async_client()
        await client.get("/foo", params={"x": "y"})
        assert route.called
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_empty_response_returns_none(self):
        respx.get(f"{BASE}/empty").mock(return_value=httpx.Response(200, content=b""))
        client = _make_async_client()
        result = await client.get("/empty")
        assert result is None
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_post_with_body(self):
        respx.post(f"{BASE}/things").mock(return_value=httpx.Response(201, json={"id": "2"}))
        client = _make_async_client()
        result = await client.post("/things", body={"name": "test"})
        assert result == {"id": "2"}
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_post_without_body(self):
        respx.post(f"{BASE}/actions").mock(return_value=httpx.Response(200, json={"ok": True}))
        client = _make_async_client()
        result = await client.post("/actions")
        assert result == {"ok": True}
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_post_with_extra_headers(self):
        route = respx.post(f"{BASE}/org").mock(return_value=httpx.Response(200, json={}))
        client = _make_async_client()
        await client.post("/org", body={}, extra_headers={"X-Active-Org-ID": "org_abc"})
        assert route.called
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_post_empty_response_returns_none(self):
        respx.post(f"{BASE}/noop").mock(return_value=httpx.Response(204, content=b""))
        client = _make_async_client()
        result = await client.post("/noop")
        assert result is None
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_patch_returns_parsed_json(self):
        respx.patch(f"{BASE}/items/1").mock(return_value=httpx.Response(200, json={"updated": True}))
        client = _make_async_client()
        result = await client.patch("/items/1", {"x": 1})
        assert result == {"updated": True}
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_returns_none(self):
        respx.delete(f"{BASE}/items/1").mock(return_value=httpx.Response(204, content=b""))
        client = _make_async_client()
        result = await client.delete("/items/1")
        assert result is None
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_authorization_header_sent(self):
        route = respx.get(f"{BASE}/check").mock(return_value=httpx.Response(200, json={}))
        client = _make_async_client()
        await client.get("/check")
        sent_headers = route.calls.last.request.headers
        expected = _build_auth_header("admin", "admin")
        assert sent_headers.get("authorization") == expected
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_organization_id_sent_as_header(self):
        route = respx.get(f"{BASE}/check").mock(return_value=httpx.Response(200, json={}))
        client = AsyncHTTPClient(BASE, "admin", "admin", organization_id="org_abc")
        await client.get("/check")
        sent_headers = route.calls.last.request.headers
        assert sent_headers.get("x-active-org-id") == "org_abc"
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_on_error_status(self):
        respx.get(f"{BASE}/err").mock(return_value=httpx.Response(404, json={"error": "nope"}))
        client = _make_async_client()
        with pytest.raises(FoundryDBError) as exc_info:
            await client.get("/err")
        assert exc_info.value.status_code == 404
        await client.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with _make_async_client() as client:
            assert isinstance(client, AsyncHTTPClient)


# ---------------------------------------------------------------------------
# FoundryDB (top-level sync client)
# ---------------------------------------------------------------------------

class TestFoundryDB:
    def test_has_expected_api_attributes(self):
        from foundrydb.services import ServicesAPI
        from foundrydb.users import UsersAPI
        from foundrydb.backups import BackupsAPI
        from foundrydb.monitoring import MonitoringAPI
        from foundrydb.organizations import OrganizationsAPI

        client = FoundryDB(BASE, "admin", "admin")
        assert isinstance(client.services, ServicesAPI)
        assert isinstance(client.users, UsersAPI)
        assert isinstance(client.backups, BackupsAPI)
        assert isinstance(client.monitoring, MonitoringAPI)
        assert isinstance(client.organizations, OrganizationsAPI)
        client.close()

    def test_context_manager(self):
        with FoundryDB(BASE, "admin", "admin") as client:
            assert isinstance(client, FoundryDB)

    def test_organization_id_wired_to_http(self):
        client = FoundryDB(BASE, "admin", "admin", organization_id="org_test")
        http = client.services._http
        assert http._client.headers.get("x-active-org-id") == "org_test"
        client.close()

    def test_custom_timeout_accepted(self):
        client = FoundryDB(BASE, "admin", "admin", timeout=60.0)
        client.close()


# ---------------------------------------------------------------------------
# AsyncFoundryDB (top-level async client)
# ---------------------------------------------------------------------------

class TestAsyncFoundryDB:
    @pytest.mark.asyncio
    async def test_has_expected_api_attributes(self):
        from foundrydb.services import AsyncServicesAPI
        from foundrydb.users import AsyncUsersAPI
        from foundrydb.backups import AsyncBackupsAPI
        from foundrydb.monitoring import AsyncMonitoringAPI
        from foundrydb.organizations import AsyncOrganizationsAPI

        client = AsyncFoundryDB(BASE, "admin", "admin")
        assert isinstance(client.services, AsyncServicesAPI)
        assert isinstance(client.users, AsyncUsersAPI)
        assert isinstance(client.backups, AsyncBackupsAPI)
        assert isinstance(client.monitoring, AsyncMonitoringAPI)
        assert isinstance(client.organizations, AsyncOrganizationsAPI)
        await client.aclose()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with AsyncFoundryDB(BASE, "admin", "admin") as client:
            assert isinstance(client, AsyncFoundryDB)

    @pytest.mark.asyncio
    async def test_organization_id_wired_to_http(self):
        client = AsyncFoundryDB(BASE, "admin", "admin", organization_id="org_abc")
        http = client.services._http
        assert http._client.headers.get("x-active-org-id") == "org_abc"
        await client.aclose()
