import pytest


@pytest.fixture(scope="module")
def login():
    yield "dbadmin"


@pytest.fixture(scope="module")
def password():
    yield "zH#y66Q7vSWvMY#p"


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, postgresql_server, resource_group, location, login, password
):
    expected = {
        "changes": {
            "new": {
                "name": postgresql_server,
                "location": location,
                "resource_group": resource_group,
                "create_mode": "Default",
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
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, postgresql_server, resource_group, location, login, password
):
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


@pytest.mark.run(order=-2)
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
