import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, file_share, storage_account, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": file_share,
                "storage_account": storage_account,
                "type": "Microsoft.Storage/storageAccounts/fileServices/shares",
            },
            "old": {},
        },
        "comment": f"File share {file_share} has been created.",
        "name": file_share,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.file_share.present(
        ctx,
        name=file_share,
        account_name=storage_account,
        resource_group=resource_group,
    )
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, file_share, storage_account, resource_group):
    metadata = {"account_name": storage_account}
    expected = {
        "changes": {
            "metadata": {"new": metadata, "old": {}},
        },
        "comment": f"File share {file_share} has been updated.",
        "name": file_share,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.file_share.present(
        ctx,
        name=file_share,
        account_name=storage_account,
        resource_group=resource_group,
        metadata=metadata,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, file_share, storage_account, resource_group):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": file_share,
            },
        },
        "comment": f"File share {file_share} has been deleted.",
        "name": file_share,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.file_share.absent(
        ctx,
        name=file_share,
        account_name=storage_account,
        resource_group=resource_group,
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
