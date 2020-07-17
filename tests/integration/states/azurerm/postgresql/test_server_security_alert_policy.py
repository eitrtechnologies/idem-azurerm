import pytest


@pytest.fixture(scope="module")
def policy_state():
    yield "Disabled"


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, postgresql_server, resource_group, policy_state):
    expected = {
        "changes": {
            "new": {
                "server_name": postgresql_server,
                "resource_group": resource_group,
                "state": policy_state,
            },
            "old": {},
        },
        "comment": f"The server security alert policy for the server {postgresql_server} has been created.",
        "name": "Default",
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server_security_alert_policy.present(
        ctx,
        server_name=postgresql_server,
        resource_group=resource_group,
        policy_state=policy_state,
    )
    assert ret == expected


@pytest.mark.run(after="test_present")
@pytest.mark.asyncio
async def test_changes(hub, ctx, postgresql_server, resource_group, policy_state):
    new_state = "Enabled"
    expected = {
        "changes": {"state": {"new": new_state, "old": policy_state,},},
        "comment": f"The server security alert policy for the server {postgresql_server} has been updated.",
        "name": "Default",
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server_security_alert_policy.present(
        ctx,
        server_name=postgresql_server,
        resource_group=resource_group,
        policy_state=new_state,
    )
    assert ret == expected
