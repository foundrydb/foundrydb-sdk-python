"""
Tests for foundrydb.users - UsersAPI (sync) and AsyncUsersAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.users import UsersAPI, AsyncUsersAPI
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import DatabaseUser, RevealPasswordResponse, FoundryDBError

BASE = "https://api.foundrydb.test"
SVC = "svc-001"

USER_PAYLOAD = {
    "username": "app_user",
    "roles": ["readWrite"],
    "created_at": "2026-01-01T00:00:00Z",
}

REVEAL_PAYLOAD = {
    "username": "app_user",
    "password": "supersecret",
    "host": "svc-001.db.foundrydb.com",
    "port": 5432,
    "database": "defaultdb",
    "connection_string": "postgresql://app_user:supersecret@svc-001.db.foundrydb.com:5432/defaultdb",
}


def make_sync_api() -> UsersAPI:
    return UsersAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncUsersAPI:
    return AsyncUsersAPI(AsyncHTTPClient(BASE, "admin", "admin"))


# ---------------------------------------------------------------------------
# Sync UsersAPI
# ---------------------------------------------------------------------------

class TestUsersAPISync:
    @respx.mock
    def test_list_returns_user_objects(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(200, json={"users": [USER_PAYLOAD]})
        )
        api = make_sync_api()
        users = api.list(SVC)
        assert len(users) == 1
        assert isinstance(users[0], DatabaseUser)
        assert users[0].username == "app_user"

    @respx.mock
    def test_list_user_fields(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(200, json={"users": [USER_PAYLOAD]})
        )
        api = make_sync_api()
        user = api.list(SVC)[0]
        assert user.username == "app_user"
        assert user.roles == ["readWrite"]
        assert user.created_at == "2026-01-01T00:00:00Z"

    @respx.mock
    def test_list_empty(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(200, json={"users": []})
        )
        api = make_sync_api()
        assert api.list(SVC) == []

    @respx.mock
    def test_list_raises_on_404(self):
        respx.get(f"{BASE}/managed-services/bad/database-users").mock(
            return_value=httpx.Response(404, json={"error": "service not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.list("bad")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_list_raises_on_500(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.list(SVC)

    @respx.mock
    def test_reveal_password_returns_response(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/app_user/reveal-password").mock(
            return_value=httpx.Response(200, json=REVEAL_PAYLOAD)
        )
        api = make_sync_api()
        resp = api.reveal_password(SVC, "app_user")
        assert isinstance(resp, RevealPasswordResponse)
        assert resp.username == "app_user"
        assert resp.password == "supersecret"
        assert resp.host == "svc-001.db.foundrydb.com"
        assert resp.port == 5432
        assert resp.database == "defaultdb"
        assert "postgresql://" in resp.connection_string

    @respx.mock
    def test_reveal_password_raw_field(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/app_user/reveal-password").mock(
            return_value=httpx.Response(200, json=REVEAL_PAYLOAD)
        )
        api = make_sync_api()
        resp = api.reveal_password(SVC, "app_user")
        assert resp.raw == REVEAL_PAYLOAD

    @respx.mock
    def test_reveal_password_raises_404(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/nobody/reveal-password").mock(
            return_value=httpx.Response(404, json={"error": "user not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.reveal_password(SVC, "nobody")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_reveal_password_raises_500(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/app_user/reveal-password").mock(
            return_value=httpx.Response(500, json={"error": "internal"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError):
            api.reveal_password(SVC, "app_user")

    @respx.mock
    def test_list_multiple_users(self):
        user2 = {"username": "readonly", "roles": ["read"], "created_at": None}
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(200, json={"users": [USER_PAYLOAD, user2]})
        )
        api = make_sync_api()
        users = api.list(SVC)
        assert len(users) == 2
        assert users[1].username == "readonly"
        assert users[1].created_at is None


# ---------------------------------------------------------------------------
# Async AsyncUsersAPI
# ---------------------------------------------------------------------------

class TestAsyncUsersAPI:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_returns_user_objects(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(200, json={"users": [USER_PAYLOAD]})
        )
        api = make_async_api()
        users = await api.list(SVC)
        assert len(users) == 1
        assert isinstance(users[0], DatabaseUser)
        assert users[0].username == "app_user"
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_empty(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(200, json={"users": []})
        )
        api = make_async_api()
        assert await api.list(SVC) == []
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_404(self):
        respx.get(f"{BASE}/managed-services/gone/database-users").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError) as exc_info:
            await api.list("gone")
        assert exc_info.value.status_code == 404
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_raises_on_500(self):
        respx.get(f"{BASE}/managed-services/{SVC}/database-users").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.list(SVC)
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_reveal_password_returns_response(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/app_user/reveal-password").mock(
            return_value=httpx.Response(200, json=REVEAL_PAYLOAD)
        )
        api = make_async_api()
        resp = await api.reveal_password(SVC, "app_user")
        assert isinstance(resp, RevealPasswordResponse)
        assert resp.username == "app_user"
        assert resp.password == "supersecret"
        assert resp.port == 5432
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_reveal_password_raises_404(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/nobody/reveal-password").mock(
            return_value=httpx.Response(404, json={"error": "user not found"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError) as exc_info:
            await api.reveal_password(SVC, "nobody")
        assert exc_info.value.status_code == 404
        await api._http.aclose()

    @respx.mock
    @pytest.mark.asyncio
    async def test_reveal_password_raises_500(self):
        respx.post(f"{BASE}/managed-services/{SVC}/database-users/app_user/reveal-password").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        api = make_async_api()
        with pytest.raises(FoundryDBError):
            await api.reveal_password(SVC, "app_user")
        await api._http.aclose()
