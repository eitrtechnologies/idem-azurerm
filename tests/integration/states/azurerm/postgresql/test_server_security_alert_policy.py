import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, postgresql_server, resource_group):
    name = "Default"
    policy_state = "Disabled"
    expected = {
        "changes": {},
        "comment": f"The server security alert policy {name} for the server {postgresql_server} is already present.",
        "name": name,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server_security_alert_policy.present(
        ctx,
        server_name=postgresql_server,
        resource_group=resource_group,
        policy_state=policy_state,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present")
@pytest.mark.asyncio
async def test_changes(hub, ctx, postgresql_server, resource_group):
    name = "Default"
    policy_state = "Disabled"
    new_state = "Enabled"
    expected = {
        "changes": {"state": {"new": new_state, "old": policy_state,},},
        "comment": f"The server security alert policy {name} for the server {postgresql_server} has been updated.",
        "name": name,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.server_security_alert_policy.present(
        ctx,
        server_name=postgresql_server,
        resource_group=resource_group,
        policy_state=new_state,
    )
    assert ret == expected
