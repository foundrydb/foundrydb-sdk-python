"""
FoundryDB SDK - HTTP client (sync via httpx, async via httpx AsyncClient).
"""
from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional, TYPE_CHECKING

import httpx

from .types import FoundryDBError

if TYPE_CHECKING:
    from .services import ServicesAPI, AsyncServicesAPI
    from .users import UsersAPI, AsyncUsersAPI
    from .backups import BackupsAPI, AsyncBackupsAPI
    from .monitoring import MonitoringAPI, AsyncMonitoringAPI
    from .organizations import OrganizationsAPI, AsyncOrganizationsAPI
    from .app_services import AppServicesAPI, AsyncAppServicesAPI


def _build_auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_error:
        body: Dict[str, Any] = {}
        try:
            body = response.json()
        except Exception:
            pass
        message = body.get("error") or body.get("message") or f"HTTP {response.status_code}"
        raise FoundryDBError(message, response.status_code, body)


class HTTPClient:
    """Synchronous HTTP client used by all API modules."""

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        timeout: float = 30.0,
        organization_id: Optional[str] = None,
    ) -> None:
        self._base_url = api_url.rstrip("/")
        self._auth_header = _build_auth_header(username, password)
        self._timeout = timeout
        default_headers: Dict[str, str] = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if organization_id:
            default_headers["X-Active-Org-ID"] = organization_id
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=default_headers,
            timeout=self._timeout,
        )

    def _url(self, path: str) -> str:
        return path if path.startswith("http") else path

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = self._client.get(path, params=params)
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    def post(
        self,
        path: str,
        body: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {}
        if body is not None:
            kwargs["content"] = json.dumps(body)
        if extra_headers:
            kwargs["headers"] = extra_headers
        resp = self._client.post(path, **kwargs)
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    def patch(self, path: str, body: Any) -> Any:
        resp = self._client.patch(path, content=json.dumps(body))
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    def delete(self, path: str) -> None:
        resp = self._client.delete(path)
        _raise_for_status(resp)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncHTTPClient:
    """Asynchronous HTTP client used by async API modules."""

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        timeout: float = 30.0,
        organization_id: Optional[str] = None,
    ) -> None:
        self._base_url = api_url.rstrip("/")
        self._auth_header = _build_auth_header(username, password)
        self._timeout = timeout
        default_headers: Dict[str, str] = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if organization_id:
            default_headers["X-Active-Org-ID"] = organization_id
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=default_headers,
            timeout=self._timeout,
        )

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = await self._client.get(path, params=params)
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    async def post(
        self,
        path: str,
        body: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {}
        if body is not None:
            kwargs["content"] = json.dumps(body)
        if extra_headers:
            kwargs["headers"] = extra_headers
        resp = await self._client.post(path, **kwargs)
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    async def patch(self, path: str, body: Any) -> Any:
        resp = await self._client.patch(path, content=json.dumps(body))
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    async def delete(self, path: str) -> None:
        resp = await self._client.delete(path)
        _raise_for_status(resp)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHTTPClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()


class FoundryDB:
    """
    FoundryDB synchronous client.

    Example::

        from foundrydb import FoundryDB

        client = FoundryDB(
            api_url="https://api.foundrydb.com",
            username="admin",
            password="admin",
        )
        services = client.services.list()

    To scope all requests to a specific organization pass ``organization_id``::

        client = FoundryDB(
            api_url="https://api.foundrydb.com",
            username="admin",
            password="admin",
            organization_id="org_abc123",
        )
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        timeout: float = 30.0,
        organization_id: Optional[str] = None,
    ) -> None:
        from .services import ServicesAPI
        from .users import UsersAPI
        from .backups import BackupsAPI
        from .monitoring import MonitoringAPI
        from .organizations import OrganizationsAPI
        from .app_services import AppServicesAPI

        http = HTTPClient(api_url, username, password, timeout, organization_id=organization_id)
        self.services: ServicesAPI = ServicesAPI(http)
        self.users: UsersAPI = UsersAPI(http)
        self.backups: BackupsAPI = BackupsAPI(http)
        self.monitoring: MonitoringAPI = MonitoringAPI(http)
        self.organizations: OrganizationsAPI = OrganizationsAPI(http)
        self.app_services: AppServicesAPI = AppServicesAPI(http)

    def close(self) -> None:
        self.services._http.close()  # type: ignore[attr-defined]

    def __enter__(self) -> "FoundryDB":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncFoundryDB:
    """
    FoundryDB asynchronous client.

    Example::

        import asyncio
        from foundrydb import AsyncFoundryDB

        async def main():
            async with AsyncFoundryDB(
                api_url="https://api.foundrydb.com",
                username="admin",
                password="admin",
            ) as client:
                services = await client.services.list()

        asyncio.run(main())

    To scope all requests to a specific organization pass ``organization_id``::

        async with AsyncFoundryDB(
            api_url="https://api.foundrydb.com",
            username="admin",
            password="admin",
            organization_id="org_abc123",
        ) as client:
            orgs = await client.organizations.list()
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        timeout: float = 30.0,
        organization_id: Optional[str] = None,
    ) -> None:
        from .services import AsyncServicesAPI
        from .users import AsyncUsersAPI
        from .backups import AsyncBackupsAPI
        from .monitoring import AsyncMonitoringAPI
        from .organizations import AsyncOrganizationsAPI
        from .app_services import AsyncAppServicesAPI

        http = AsyncHTTPClient(api_url, username, password, timeout, organization_id=organization_id)
        self.services: AsyncServicesAPI = AsyncServicesAPI(http)
        self.users: AsyncUsersAPI = AsyncUsersAPI(http)
        self.backups: AsyncBackupsAPI = AsyncBackupsAPI(http)
        self.monitoring: AsyncMonitoringAPI = AsyncMonitoringAPI(http)
        self.organizations: AsyncOrganizationsAPI = AsyncOrganizationsAPI(http)
        self.app_services: AsyncAppServicesAPI = AsyncAppServicesAPI(http)

    async def aclose(self) -> None:
        await self.services._http.aclose()  # type: ignore[attr-defined]

    async def __aenter__(self) -> "AsyncFoundryDB":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
