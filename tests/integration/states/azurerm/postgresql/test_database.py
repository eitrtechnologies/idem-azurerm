import pytest
import string
import random


@pytest.fixture(scope="session")
def postgresql_db():
    yield "psql-db-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, postgresql_db, postgresql_server, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": postgresql_db,
                "type": "Microsoft.DBforPostgreSQL/servers/databases",
                "charset": "UTF8",
                "collation": "English_United States.1252",
            },
            "old": {},
        },
        "comment": f"Database {postgresql_db} has been created.",
        "name": postgresql_db,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.database.present(
        ctx,
        name=postgresql_db,
        server_name=postgresql_server,
        resource_group=resource_group,
    )
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, postgresql_db, postgresql_server, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": postgresql_db,},},
        "comment": f"Database {postgresql_db} has been deleted.",
        "name": postgresql_db,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.database.absent(
        ctx, postgresql_db, postgresql_server, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
