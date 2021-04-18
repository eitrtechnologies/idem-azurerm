import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, availability_set, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": availability_set,
                "sku": {"name": "Classic"},
                "type": "Microsoft.Compute/availabilitySets",
                "location": "eastus",
                "platform_fault_domain_count": 3,
                "platform_update_domain_count": 5,
            },
            "old": {},
        },
        "comment": f"Availability set {availability_set} has been created.",
        "name": availability_set,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.availability_set.present(
        ctx, name=availability_set, resource_group=resource_group
    )
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, availability_set, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Availability set {availability_set} has been updated.",
        "name": availability_set,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.availability_set.present(
        ctx, name=availability_set, resource_group=resource_group, tags=tags
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, availability_set, resource_group):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": availability_set,
            },
        },
        "comment": f"Availability set {availability_set} has been deleted.",
        "name": availability_set,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.availability_set.absent(
        ctx, availability_set, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
