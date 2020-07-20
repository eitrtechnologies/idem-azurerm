import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, storage_account):
    sku = "Standard_LRS"
    kind = "StorageV2"
    expected = {
        "changes": {
            "new": {
                "name": storage_account,
                "location": location,
                "kind": kind,
                "resource_group": resource_group,
                "sku": sku,
            },
            "old": {},
        },
        "comment": f"Storage account {storage_account} has been created.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.present(
        ctx,
        name=storage_account,
        resource_group=resource_group,
        location=location,
        kind=kind,
        sku=sku,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, tags, location, storage_account):
    sku = "Standard_LRS"
    kind = "StorageV2"
    expected = {
        "changes": {"tags": {"new": tags,},},
        "comment": f"Storage account {storage_account} has been updated.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.present(
        ctx,
        name=storage_account,
        resource_group=resource_group,
        location=location,
        sku=sku,
        kind=kind,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, storage_account):
    expected = {
        "changes": {"new": {}, "old": {"name": storage_account,},},
        "comment": f"Storage account {storage_account} has been deleted.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.absent(
        ctx, storage_account, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
