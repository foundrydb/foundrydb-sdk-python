"""
Tests for foundrydb.app_services - AppServicesAPI (sync) and AsyncAppServicesAPI (async).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from foundrydb.app_services import AppServicesAPI, AsyncAppServicesAPI
from foundrydb.client import HTTPClient, AsyncHTTPClient
from foundrydb.types import (
    AppContainerConfig,
    AppService,
    AuthConfigurationWithKeys,
    AuthEnableRequest,
    AuthSigningKey,
    FoundryDBError,
    IdpProviderRequest,
    SmtpConfig,
    AuthTheme,
)

BASE = "https://api.foundrydb.test"

APP_PAYLOAD = {
    "id": "app-001",
    "name": "my-app",
    "service_kind": "app",
    "status": "Running",
    "zone": "se-sto1",
    "plan_name": "tier-2",
    "storage_size_gb": 10,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
    "app_config": {
        "image_ref": "docker.io/traefik/whoami:latest",
        "container_port": 80,
    },
}

AUTH_CONFIG_PAYLOAD = {
    "id": "auth-001",
    "app_service_id": "app-001",
    "database_service_id": "db-001",
    "attachment_id": "att-001",
    "issuer_url": "https://auth-abc123.foundrydb.com",
    "fallback_domain": "auth-abc123.foundrydb.com",
    "status": "Active",
    "theme": {
        "display_name": "Acme",
        "brand_color": "#4F46E5",
    },
    "idp_providers": [
        {"provider": "google", "client_id": "client-xyz", "display_name": "Sign in with Google"},
    ],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}

AUTH_WITH_KEYS_PAYLOAD = {
    "auth": AUTH_CONFIG_PAYLOAD,
    "signing_keys": [
        {
            "id": "key-001",
            "auth_configuration_id": "auth-001",
            "kid": "kid-abc",
            "algorithm": "RS256",
            "status": "active",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ],
}

SIGNING_KEY_PAYLOAD = {
    "id": "key-002",
    "auth_configuration_id": "auth-001",
    "kid": "kid-new",
    "algorithm": "RS256",
    "status": "active",
    "created_at": "2026-06-01T00:00:00Z",
    "updated_at": "2026-06-01T00:00:00Z",
}


def make_sync_api() -> AppServicesAPI:
    return AppServicesAPI(HTTPClient(BASE, "admin", "admin"))


def make_async_api() -> AsyncAppServicesAPI:
    return AsyncAppServicesAPI(AsyncHTTPClient(BASE, "admin", "admin"))


def make_smtp() -> SmtpConfig:
    return SmtpConfig(
        host="smtp.example.com",
        port=587,
        username="noreply@example.com",
        password="secret",
        from_address="noreply@example.com",
        from_name="Example Login",
    )


def make_enable_req() -> AuthEnableRequest:
    return AuthEnableRequest(
        attachment_id="att-001",
        issuer_domain_choice="fallback",
        smtp=make_smtp(),
        theme=AuthTheme(display_name="Acme", brand_color="#4F46E5"),
    )


# ---------------------------------------------------------------------------
# Sync AppServicesAPI
# ---------------------------------------------------------------------------

class TestAppServicesAPISync:
    @respx.mock
    def test_list_returns_app_service_objects(self):
        respx.get(f"{BASE}/app-services").mock(
            return_value=httpx.Response(200, json={"app_services": [APP_PAYLOAD]})
        )
        api = make_sync_api()
        apps = api.list()
        assert len(apps) == 1
        app = apps[0]
        assert isinstance(app, AppService)
        assert app.id == "app-001"
        assert app.name == "my-app"
        assert app.status == "Running"
        assert app.app_config is not None
        assert app.app_config.image_ref == "docker.io/traefik/whoami:latest"
        assert app.app_config.container_port == 80

    @respx.mock
    def test_list_empty(self):
        respx.get(f"{BASE}/app-services").mock(
            return_value=httpx.Response(200, json={"app_services": []})
        )
        api = make_sync_api()
        assert api.list() == []

    @respx.mock
    def test_get_returns_app(self):
        respx.get(f"{BASE}/app-services/app-001").mock(
            return_value=httpx.Response(200, json=APP_PAYLOAD)
        )
        api = make_sync_api()
        app = api.get("app-001")
        assert isinstance(app, AppService)
        assert app.id == "app-001"
        assert app.zone == "se-sto1"

    @respx.mock
    def test_get_raises_on_404(self):
        respx.get(f"{BASE}/app-services/nonexistent").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        with pytest.raises(FoundryDBError) as exc_info:
            api.get("nonexistent")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_create_app(self):
        respx.post(f"{BASE}/app-services").mock(
            return_value=httpx.Response(201, json=APP_PAYLOAD)
        )
        api = make_sync_api()
        cfg = AppContainerConfig(image_ref="docker.io/traefik/whoami:latest", container_port=80)
        app = api.create(name="my-app", plan_name="tier-2", app_config=cfg)
        assert isinstance(app, AppService)
        assert app.id == "app-001"

    @respx.mock
    def test_delete_app(self):
        respx.delete(f"{BASE}/app-services/app-001").mock(
            return_value=httpx.Response(202)
        )
        api = make_sync_api()
        api.delete("app-001")  # should not raise

    # ------------------------------------------------------------------
    # Auth methods - sync
    # ------------------------------------------------------------------

    @respx.mock
    def test_enable_app_service_auth(self):
        respx.post(f"{BASE}/app-services/app-001/auth/enable").mock(
            return_value=httpx.Response(201, json=AUTH_WITH_KEYS_PAYLOAD)
        )
        api = make_sync_api()
        result = api.enable_app_service_auth("app-001", make_enable_req())
        assert isinstance(result, AuthConfigurationWithKeys)
        assert result.auth is not None
        assert result.auth.id == "auth-001"
        assert result.auth.status == "Active"
        assert result.auth.issuer_url == "https://auth-abc123.foundrydb.com"
        assert len(result.signing_keys) == 1
        assert result.signing_keys[0].kid == "kid-abc"
        assert result.signing_keys[0].algorithm == "RS256"

    @respx.mock
    def test_enable_auth_with_idp_providers(self):
        respx.post(f"{BASE}/app-services/app-001/auth/enable").mock(
            return_value=httpx.Response(201, json=AUTH_WITH_KEYS_PAYLOAD)
        )
        api = make_sync_api()
        req = AuthEnableRequest(
            attachment_id="att-001",
            issuer_domain_choice="fallback",
            smtp=make_smtp(),
            idp_providers=[
                IdpProviderRequest(
                    provider="google",
                    client_id="client-xyz",
                    client_secret="secret-xyz",
                    display_name="Sign in with Google",
                )
            ],
        )
        result = api.enable_app_service_auth("app-001", req)
        assert result.auth is not None
        assert len(result.auth.idp_providers) == 1
        assert result.auth.idp_providers[0].provider == "google"
        assert result.auth.idp_providers[0].client_id == "client-xyz"

    @respx.mock
    def test_get_app_service_auth(self):
        respx.get(f"{BASE}/app-services/app-001/auth").mock(
            return_value=httpx.Response(200, json=AUTH_WITH_KEYS_PAYLOAD)
        )
        api = make_sync_api()
        result = api.get_app_service_auth("app-001")
        assert result is not None
        assert isinstance(result, AuthConfigurationWithKeys)
        assert result.auth is not None
        assert result.auth.app_service_id == "app-001"
        assert result.auth.theme is not None
        assert result.auth.theme.display_name == "Acme"

    @respx.mock
    def test_get_app_service_auth_returns_none_on_404(self):
        respx.get(f"{BASE}/app-services/app-001/auth").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_sync_api()
        result = api.get_app_service_auth("app-001")
        assert result is None

    @respx.mock
    def test_disable_app_service_auth(self):
        respx.post(f"{BASE}/app-services/app-001/auth/disable").mock(
            return_value=httpx.Response(200, json={"status": "Disabled"})
        )
        api = make_sync_api()
        status = api.disable_app_service_auth("app-001")
        assert status == "Disabled"

    @respx.mock
    def test_rotate_app_service_auth_key(self):
        respx.post(f"{BASE}/app-services/app-001/auth/rotate-key").mock(
            return_value=httpx.Response(200, json={"signing_key": SIGNING_KEY_PAYLOAD})
        )
        api = make_sync_api()
        key = api.rotate_app_service_auth_key("app-001")
        assert isinstance(key, AuthSigningKey)
        assert key.id == "key-002"
        assert key.kid == "kid-new"
        assert key.algorithm == "RS256"
        assert key.status == "active"

    @respx.mock
    def test_revoke_app_service_auth_session(self):
        respx.post(f"{BASE}/app-services/app-001/auth/sessions/sess-abc/revoke").mock(
            return_value=httpx.Response(202, json={"task_id": "task-xyz"})
        )
        api = make_sync_api()
        task_id = api.revoke_app_service_auth_session("app-001", "sess-abc")
        assert task_id == "task-xyz"

    def test_auth_enable_request_to_dict_excludes_none_theme(self):
        req = AuthEnableRequest(
            attachment_id="att-001",
            issuer_domain_choice="fallback",
            smtp=make_smtp(),
        )
        body = req.to_dict()
        assert "theme" not in body
        assert body["attachment_id"] == "att-001"
        assert body["issuer_domain_choice"] == "fallback"
        assert body["smtp"]["host"] == "smtp.example.com"
        assert body["smtp"]["password"] == "secret"

    def test_auth_enable_request_to_dict_with_idp(self):
        req = AuthEnableRequest(
            attachment_id="att-001",
            issuer_domain_choice="fallback",
            smtp=make_smtp(),
            idp_providers=[
                IdpProviderRequest(
                    provider="github",
                    client_id="gh-id",
                    client_secret="gh-secret",
                )
            ],
        )
        body = req.to_dict()
        assert "idp_providers" in body
        assert len(body["idp_providers"]) == 1
        assert body["idp_providers"][0]["provider"] == "github"
        assert body["idp_providers"][0]["client_secret"] == "gh-secret"

    def test_signing_key_from_dict(self):
        key = AuthSigningKey.from_dict(SIGNING_KEY_PAYLOAD)
        assert key.id == "key-002"
        assert key.kid == "kid-new"
        assert key.algorithm == "RS256"
        assert key.auth_configuration_id == "auth-001"

    def test_auth_configuration_idp_providers_parsed(self):
        from foundrydb.types import AuthConfiguration
        cfg = AuthConfiguration.from_dict(AUTH_CONFIG_PAYLOAD)
        assert len(cfg.idp_providers) == 1
        assert cfg.idp_providers[0].provider == "google"
        assert cfg.idp_providers[0].client_id == "client-xyz"

    def test_smtp_insecure_skip_verify_omitted_by_default(self):
        smtp = make_smtp()
        body = smtp.to_dict()
        assert "insecure_skip_verify" not in body

    def test_smtp_insecure_skip_verify_included_when_true(self):
        smtp = SmtpConfig(
            host="smtp.example.com",
            port=587,
            username="u",
            password="p",
            from_address="a@b.com",
            insecure_skip_verify=True,
        )
        body = smtp.to_dict()
        assert body["insecure_skip_verify"] is True


# ---------------------------------------------------------------------------
# Async AppServicesAPI
# ---------------------------------------------------------------------------

class TestAppServicesAPIAsync:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_returns_app_service_objects(self):
        respx.get(f"{BASE}/app-services").mock(
            return_value=httpx.Response(200, json={"app_services": [APP_PAYLOAD]})
        )
        api = make_async_api()
        apps = await api.list()
        assert len(apps) == 1
        assert isinstance(apps[0], AppService)
        assert apps[0].id == "app-001"

    @respx.mock
    @pytest.mark.asyncio
    async def test_enable_app_service_auth(self):
        respx.post(f"{BASE}/app-services/app-001/auth/enable").mock(
            return_value=httpx.Response(201, json=AUTH_WITH_KEYS_PAYLOAD)
        )
        api = make_async_api()
        result = await api.enable_app_service_auth("app-001", make_enable_req())
        assert isinstance(result, AuthConfigurationWithKeys)
        assert result.auth is not None
        assert result.auth.id == "auth-001"
        assert len(result.signing_keys) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_app_service_auth(self):
        respx.get(f"{BASE}/app-services/app-001/auth").mock(
            return_value=httpx.Response(200, json=AUTH_WITH_KEYS_PAYLOAD)
        )
        api = make_async_api()
        result = await api.get_app_service_auth("app-001")
        assert result is not None
        assert result.auth is not None
        assert result.auth.status == "Active"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_app_service_auth_returns_none_on_404(self):
        respx.get(f"{BASE}/app-services/app-001/auth").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        api = make_async_api()
        result = await api.get_app_service_auth("app-001")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_disable_app_service_auth(self):
        respx.post(f"{BASE}/app-services/app-001/auth/disable").mock(
            return_value=httpx.Response(200, json={"status": "Disabled"})
        )
        api = make_async_api()
        status = await api.disable_app_service_auth("app-001")
        assert status == "Disabled"

    @respx.mock
    @pytest.mark.asyncio
    async def test_rotate_app_service_auth_key(self):
        respx.post(f"{BASE}/app-services/app-001/auth/rotate-key").mock(
            return_value=httpx.Response(200, json={"signing_key": SIGNING_KEY_PAYLOAD})
        )
        api = make_async_api()
        key = await api.rotate_app_service_auth_key("app-001")
        assert isinstance(key, AuthSigningKey)
        assert key.kid == "kid-new"

    @respx.mock
    @pytest.mark.asyncio
    async def test_revoke_app_service_auth_session(self):
        respx.post(f"{BASE}/app-services/app-001/auth/sessions/sess-abc/revoke").mock(
            return_value=httpx.Response(202, json={"task_id": "task-xyz"})
        )
        api = make_async_api()
        task_id = await api.revoke_app_service_auth_session("app-001", "sess-abc")
        assert task_id == "task-xyz"
