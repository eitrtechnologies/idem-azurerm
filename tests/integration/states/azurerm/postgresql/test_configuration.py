import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present_and_changes(hub, ctx, postgresql_server, resource_group):
    config_name = "log_retention_days"
    val = "5"
    old_val = "3"
    expected = {
        "changes": {
            "value": {"new": val, "old": old_val},
        },
        "comment": f"Configuration Setting {config_name} has been updated.",
        "name": config_name,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.configuration.present(
        ctx,
        name=config_name,
        server_name=postgresql_server,
        resource_group=resource_group,
        value=val,
    )
    assert ret == expected
