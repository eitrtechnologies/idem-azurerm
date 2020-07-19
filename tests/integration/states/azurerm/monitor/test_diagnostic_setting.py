import pytest
import random
import string


@pytest.fixture(scope="session")
def diag_setting():
    yield "idem-diag-setting-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="module")
def metrics():
    yield [
        {
            "category": "AllMetrics",
            "enabled": True,
            "retention_policy": {"enabled": True, "days": 11},
        }
    ]


@pytest.fixture(scope="module")
def logs():
    yield [
        {
            "category": "VMProtectionAlerts",
            "enabled": True,
            "retention_policy": {"enabled": True, "days": 1},
        }
    ]


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, diag_setting, metrics, logs, resource_group, vnet, storage_account
):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    resource_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}"
    storage_account_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account}"
    expected = {
        "changes": {
            "new": {
                "name": diag_setting,
                "resource_uri": resource_uri,
                "metrics": metrics,
                "logs": logs,
                "storage_account_id": storage_account_id,
            },
            "old": {},
        },
        "comment": f"Diagnostic setting {diag_setting} has been created.",
        "name": diag_setting,
        "result": True,
    }
    ret = await hub.states.azurerm.monitor.diagnostic_setting.present(
        ctx,
        name=diag_setting,
        resource_uri=resource_uri,
        metrics=metrics,
        logs=logs,
        storage_account_id=storage_account_id,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub,
    ctx,
    diag_setting,
    metrics,
    logs,
    resource_group,
    vnet,
    storage_account,
    log_analytics_workspace,
):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    resource_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}"
    storage_account_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account}"
    workspace_id = f"/subscriptions/{subscription_id}/resourcegroups/{resource_group}/providers/microsoft.operationalinsights/workspaces/{log_analytics_workspace}"
    expected = {
        "changes": {"workspace_id": {"new": workspace_id, "old": None},},
        "comment": f"Diagnostic setting {diag_setting} has been updated.",
        "name": diag_setting,
        "result": True,
    }
    ret = await hub.states.azurerm.monitor.diagnostic_setting.present(
        ctx,
        name=diag_setting,
        resource_uri=resource_uri,
        metrics=metrics,
        logs=logs,
        storage_account_id=storage_account_id,
        workspace_id=workspace_id,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, diag_setting, resource_group, vnet):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    resource_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}"
    expected = {
        "changes": {"new": {}, "old": {"name": diag_setting,},},
        "comment": f"Diagnostic setting {diag_setting} has been deleted.",
        "name": diag_setting,
        "result": True,
    }
    ret = await hub.states.azurerm.monitor.diagnostic_setting.absent(
        ctx, name=diag_setting, resource_uri=resource_uri
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
