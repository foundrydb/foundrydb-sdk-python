"""
Live integration tests for the FoundryDB Python SDK.

Usage:
    python3 test_live.py
"""
import asyncio
import sys
import os
import traceback

# Add the SDK directory to the path so we import the local package.
sys.path.insert(0, os.path.dirname(__file__))

from foundrydb import FoundryDB, AsyncFoundryDB

API_URL = "https://api.foundrydb.com"
USERNAME = "admin"
PASSWORD = "0BYjYyWhb5MW96LVIXqE"

# Known live services and their expected database types.
EXPECTED_SERVICES = {
    "a65ea369-7a0d-460f-8289-09bf031ed7fc": "postgresql",
    "0f535f8e-fe90-4c61-86a6-9291e4153921": "mysql",
    "b812422b-1869-4e9c-b698-9fdfcbebf75d": "mongodb",
    "c5f66c4f-dee3-49e5-8b77-5356f875043b": "valkey",
    "190d4aaf-3224-48f9-a144-d4cfe09b45e8": "kafka",
    "fd401c8a-97c5-429e-9e9d-bb503e664856": "opensearch",
    "1ad021f7-a954-44a8-b829-af6501045a3e": "mssql",
}

passed = 0
failed = 0


def report(label: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    status = "PASS" if ok else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    if ok:
        passed += 1
    else:
        failed += 1


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------

def test_sync() -> None:
    print("\n=== Sync client (FoundryDB) ===\n")

    client = FoundryDB(api_url=API_URL, username=USERNAME, password=PASSWORD)

    # Test list_organizations (via client.organizations.list())
    print("-- list_organizations --")
    try:
        orgs = client.organizations.list()
        print(f"  Organizations returned: {len(orgs)}")
        for org in orgs:
            print(f"    id={org.id!r}  name={org.name!r}  is_personal={org.is_personal}")
        report("list_organizations returns list", isinstance(orgs, list))
        report("list_organizations non-empty", len(orgs) > 0)
        if orgs:
            first = orgs[0]
            report("Organization.id is a non-empty string", bool(first.id))
            report("Organization.name is a non-empty string", bool(first.name))
            report("Organization.slug is a non-empty string", bool(first.slug))
            report("Organization.is_personal is bool", isinstance(first.is_personal, bool))
    except Exception as exc:
        report("list_organizations", False, f"Exception: {exc}")
        traceback.print_exc()

    # Test get_service for each known service
    print("\n-- get_service (per engine) --")
    for service_id, expected_type in EXPECTED_SERVICES.items():
        try:
            svc = client.services.get(service_id)
            id_ok = svc.id == service_id
            type_ok = svc.database_type == expected_type
            status_ok = svc.status == "Running"
            report(
                f"get_service({expected_type}) id matches",
                id_ok,
                f"got={svc.id!r}",
            )
            report(
                f"get_service({expected_type}) database_type matches",
                type_ok,
                f"got={svc.database_type!r} expected={expected_type!r}",
            )
            report(
                f"get_service({expected_type}) status==Running",
                status_ok,
                f"got={svc.status!r}",
            )
        except Exception as exc:
            report(f"get_service({expected_type})", False, f"Exception: {exc}")
            traceback.print_exc()

    # Test list_services
    print("\n-- list_services --")
    try:
        services = client.services.list()
        print(f"  Total services returned: {len(services)}")
        for svc in services:
            print(f"    id={svc.id!r}  type={svc.database_type!r}  status={svc.status!r}  name={svc.name!r}")

        service_ids = {svc.id for svc in services}
        all_present = all(sid in service_ids for sid in EXPECTED_SERVICES)

        report("list_services returns list", isinstance(services, list))
        report("list_services contains all 7 known services", all_present)

        missing = [sid for sid in EXPECTED_SERVICES if sid not in service_ids]
        if missing:
            for sid in missing:
                print(f"    MISSING: {sid} ({EXPECTED_SERVICES[sid]})")
    except Exception as exc:
        report("list_services", False, f"Exception: {exc}")
        traceback.print_exc()

    client.close()


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------

async def test_async() -> None:
    print("\n=== Async client (AsyncFoundryDB) ===\n")

    async with AsyncFoundryDB(api_url=API_URL, username=USERNAME, password=PASSWORD) as client:

        # Async list_organizations
        print("-- async list_organizations --")
        try:
            orgs = await client.organizations.list()
            print(f"  Organizations returned: {len(orgs)}")
            for org in orgs:
                print(f"    id={org.id!r}  name={org.name!r}  is_personal={org.is_personal}")
            report("async list_organizations returns list", isinstance(orgs, list))
            report("async list_organizations non-empty", len(orgs) > 0)
            if orgs:
                first = orgs[0]
                report("async Organization.id non-empty", bool(first.id))
                report("async Organization.slug non-empty", bool(first.slug))
        except Exception as exc:
            report("async list_organizations", False, f"Exception: {exc}")
            traceback.print_exc()

        # Async get_service for each engine
        print("\n-- async get_service (per engine) --")
        for service_id, expected_type in EXPECTED_SERVICES.items():
            try:
                svc = await client.services.get(service_id)
                id_ok = svc.id == service_id
                type_ok = svc.database_type == expected_type
                status_ok = svc.status == "Running"
                report(
                    f"async get_service({expected_type}) id matches",
                    id_ok,
                    f"got={svc.id!r}",
                )
                report(
                    f"async get_service({expected_type}) database_type matches",
                    type_ok,
                    f"got={svc.database_type!r} expected={expected_type!r}",
                )
                report(
                    f"async get_service({expected_type}) status==Running",
                    status_ok,
                    f"got={svc.status!r}",
                )
            except Exception as exc:
                report(f"async get_service({expected_type})", False, f"Exception: {exc}")
                traceback.print_exc()

        # Async list_services
        print("\n-- async list_services --")
        try:
            services = await client.services.list()
            print(f"  Total services returned: {len(services)}")
            service_ids = {svc.id for svc in services}
            all_present = all(sid in service_ids for sid in EXPECTED_SERVICES)
            report("async list_services returns list", isinstance(services, list))
            report("async list_services contains all 7 known services", all_present)
        except Exception as exc:
            report("async list_services", False, f"Exception: {exc}")
            traceback.print_exc()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_sync()
    asyncio.run(test_async())

    print("\n" + "=" * 50)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED ({failed} failures)")
        sys.exit(1)
