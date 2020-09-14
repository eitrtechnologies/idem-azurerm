import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, resource_group, location, storage_account, storage_container
):
    public_access = "Blob"
    expected = {
        "changes": {
            "new": {
                "name": storage_container,
                "public_access": public_access,
                "deleted": False,
                "has_immutability_policy": False,
                "has_legal_hold": False,
                "remaining_retention_days": 0,
                "type": "Microsoft.Storage/storageAccounts/blobServices/containers",
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
        location=location,
        resource_group=resource_group,
        public_access=public_access,
    )
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(
    order=4, after="test_present", before="test_policy_present_and_changes"
)
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, resource_group, location, storage_account, storage_container
):
    public_access = "Blob"
    metadata = {"Company": "EITR Technologies"}
    expected = {
        "changes": {"metadata": {"new": metadata,},},
        "comment": f"Blob container {storage_container} has been updated.",
        "name": storage_container,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.container.present(
        ctx,
        name=storage_container,
        account=storage_account,
        resource_group=resource_group,
        location=location,
        metadata=metadata,
        public_access=public_access,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_changes", before="test_absent")
@pytest.mark.asyncio
async def test_immutability_policy_present_and_changes(
    hub, ctx, resource_group, storage_account, storage_container
):
    immutability_period = 10
    expected = {
        "changes": {
            "immutability_period_since_creation_in_days": {"old": 0, "new": 10},
        },
        "comment": f"The immutability policy of the blob container {storage_container} has been updated.",
        "name": storage_container,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.container.immutability_policy_present(
        ctx,
        name=storage_container,
        account=storage_account,
        resource_group=resource_group,
        immutability_period=immutability_period,
    )
    assert ret == expected
    expected["changes"] = {}
    expected[
        "comment"
    ] = f"The immutability policy of the blob container {storage_container} is already present."
    ret = await hub.states.azurerm.storage.container.immutability_policy_present(
        ctx,
        name=storage_container,
        account=storage_account,
        resource_group=resource_group,
        immutability_period=immutability_period,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, storage_account, storage_container):
    expected = {
        "changes": {"new": {}, "old": {"name": storage_container,},},
        "comment": f"Storage container {storage_container} has been deleted.",
        "name": storage_container,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.container.absent(
        ctx, storage_container, storage_account, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
