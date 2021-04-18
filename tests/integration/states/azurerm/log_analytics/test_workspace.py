import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, log_analytics_workspace):
    expected = {
        "changes": {
            "new": {
                "name": log_analytics_workspace,
                "location": location,
                "provisioning_state": "Succeeded",
                "public_network_access_for_ingestion": "Enabled",
                "public_network_access_for_query": "Enabled",
                "retention_in_days": 30,
                "sku": {"max_capacity_reservation_level": 3000, "name": "pergb2018"},
                "type": "Microsoft.OperationalInsights/workspaces",
                "workspace_capping": {"daily_quota_gb": -1.0},
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

    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("customer_id")
    ret["changes"]["new"]["sku"].pop("last_sku_update")
    ret["changes"]["new"]["workspace_capping"].pop("quota_next_reset_time")
    ret["changes"]["new"]["workspace_capping"].pop("data_ingestion_status")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, log_analytics_workspace):
    retention = 10
    expected = {
        "changes": {
            "retention_in_days": {"new": 10, "old": 30},
        },
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
        "changes": {
            "new": {},
            "old": {
                "name": log_analytics_workspace,
            },
        },
        "comment": f"Log Analytics Workspace {log_analytics_workspace} has been deleted.",
        "name": log_analytics_workspace,
        "result": True,
    }
    ret = await hub.states.azurerm.log_analytics.workspace.absent(
        ctx, name=log_analytics_workspace, resource_group=resource_group, force=True
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
