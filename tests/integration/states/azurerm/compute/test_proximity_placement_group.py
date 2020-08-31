import pytest
import random
import string


@pytest.fixture(scope="session")
def ppg():
    yield "ppg-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_present(hub, ctx, ppg, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": ppg,
                "resource_group": resource_group,
                "tags": None,
                "proximity_placement_group_type": "standard",
            },
            "old": {},
        },
        "comment": f"Proximity placement group {ppg} has been created.",
        "name": ppg,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.proximity_placement_group.present(
        ctx, name=ppg, resource_group=resource_group
    )
    assert ret == expected


@pytest.mark.run(order=2, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, ppg, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Proximity placement group {ppg} has been updated.",
        "name": ppg,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.proximity_placement_group.present(
        ctx, name=ppg, resource_group=resource_group, tags=tags
    )
    assert ret == expected


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_absent(hub, ctx, ppg, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": ppg,},},
        "comment": f"Proximity placement group {ppg} has been deleted.",
        "name": ppg,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.proximity_placement_group.absent(
        ctx, ppg, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
