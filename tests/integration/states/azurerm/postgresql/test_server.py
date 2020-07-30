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
                "resource_group": resource_group,
                "create_mode": "Default",
                "sku": {"name": sku},
                "administrator_login": login,
                "administrator_login_password": "REDACTED",
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
