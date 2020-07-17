import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, log_analytics_workspace):
    expected = {
        "changes": {
            "new": {
                "name": log_analytics_workspace,
                "location": location,
                "resource_group": resource_group,
            },
            "old": {},
        },
        "comment": f"Log Analytics Workspace {log_analytics_workspace} has been created.",
        "name": log_analytics_workspace,
        "result": True,
    }
    ret = await hub.states.azurerm.log_analytics.workspace.present(
        ctx,
        name=log_analytics_workspace,
        resource_group=resource_group,
        location=location,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, log_analytics_workspace):
    retention = 10
    expected = {
        "changes": {"retention_in_days": {"new": 10, "old": 30},},
        "comment": f"Log Analytics Workspace {log_analytics_workspace} has been updated.",
        "name": log_analytics_workspace,
        "result": True,
    }
    ret = await hub.states.azurerm.log_analytics.workspace.present(
        ctx,
        name=log_analytics_workspace,
        resource_group=resource_group,
        location=location,
        retention=retention,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, log_analytics_workspace):
    expected = {
        "changes": {"new": {}, "old": {"name": log_analytics_workspace,},},
        "comment": f"Log Analytics Workspace {log_analytics_workspace} has been deleted.",
        "name": log_analytics_workspace,
        "result": True,
    }
    ret = await hub.states.azurerm.log_analytics.workspace.absent(
        ctx, log_analytics_workspace, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
