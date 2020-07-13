import pytest
'''
--------
      ID: Ensure container exists
Function: azurerm.storage.container.present
  Result: True
 Comment: Blob container testcontainer has been created.
 Changes: old:
    ----------
new:
    ----------
    name:
        testcontainer
    account:
        eitrdelete
    resource_group:
        rg-tests
    public_access:
        Blob
'''
@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, storage_account, storage_container):
    public_access = 'Standard_LRS'
    expected = {
        "changes": {
            "new": {
                "name": storage_container,
                "resource_group": resource_group,
                "public_access": public_access,
                "account": storage_account,
            },
            "old": {},
        },
        "comment": f"Blob container {storage_container} has been created.",
        "name": storage_container,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.container.present(
        ctx,
        name=storage_container,
        account=storage_account,
        resource_group=resource_group,
        public_access=public_access,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, tags, location, storage_account):
    sku = 'Standard_LRS'
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
        "changes": {
            "new": {},
            "old": {
                "name": storage_account,
            },
        },
        "comment": f"Storage account {storage_account} has been deleted.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.absent(ctx, storage_account, resource_group)
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
