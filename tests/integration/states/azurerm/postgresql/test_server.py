import pytest
import random
import string


@pytest.fixture(scope="session")
def password():
    yield "#" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    ) + "!"


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, postgresql_server, resource_group, location, password):
    login = "dbadmin"
    sku = "GP_Gen5_4"
    expected = {
        "changes": {
            "new": {
                "name": postgresql_server,
                "location": location,
                "sku": {
                    "name": sku,
                    "capacity": 4,
                    "family": "Gen5",
                    "tier": "GeneralPurpose",
                },
                "administrator_login": login,
                "replica_capacity": 5,
                "replication_role": "None",
                "type": "Microsoft.DBforPostgreSQL/servers",
                "user_visible_state": "Ready",
                "private_endpoint_connections": [],
                "public_network_access": "Enabled",
                "replica_capacity": 5,
                "replication_role": "None",
                "ssl_enforcement": "Enabled",
                "storage_profile": {
                    "backup_retention_days": 7,
                    "geo_redundant_backup": "Disabled",
                    "storage_autogrow": "Disabled",
                    "storage_mb": 5120,
                },
                "infrastructure_encryption": "Disabled",
                "master_server_id": "",
                "minimal_tls_version": "TLSEnforcementDisabled",
                "byok_enforcement": "Disabled",
                "fully_qualified_domain_name": f"{postgresql_server}.postgres.database.azure.com",
            },
            "old": {},
        },
        "comment": f"Server {postgresql_server} has been created.",
        "name": postgresql_server,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server.present(
        ctx,
        name=postgresql_server,
        resource_group=resource_group,
        location=location,
        login=login,
        login_password=password,
        sku=sku,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("version")
    ret["changes"]["new"].pop("earliest_restore_date")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, postgresql_server, resource_group, location, password):
    login = "dbadmin"
    ssl_enforcement = "Disabled"
    expected = {
        "changes": {
            "ssl_enforcement": {"new": "Disabled", "old": "Enabled"},
            "administrator_login_password": {"new": "REDACTED"},
        },
        "comment": f"Server {postgresql_server} has been updated.",
        "name": postgresql_server,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server.present(
        ctx,
        name=postgresql_server,
        resource_group=resource_group,
        location=location,
        login=login,
        login_password=password,
        ssl_enforcement=ssl_enforcement,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, postgresql_server, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": postgresql_server,},},
        "comment": f"Server {postgresql_server} has been deleted.",
        "name": postgresql_server,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server.absent(
        ctx, postgresql_server, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
