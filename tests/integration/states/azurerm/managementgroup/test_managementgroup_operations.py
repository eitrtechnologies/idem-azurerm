import pytest
import random
import string


@pytest.fixture(scope="module")
def management_group():
    yield "idem-mgroup-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=1)
@pytest.mark.asyncio
async def test_present(hub, ctx, management_group):
    expected = {
        "changes": {"new": {"name": management_group,}, "old": {},},
        "comment": f"Management Group {management_group} has been created.",
        "name": management_group,
        "result": True,
    }
    ret = await hub.states.azurerm.managementgroup.operations.present(
        ctx, name=management_group,
    )
    assert ret == expected


@pytest.mark.run(order=1, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, management_group):
    display_name = "idem-mgroup-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
    expected = {
        "changes": {"display_name": {"new": display_name, "old": management_group},},
        "comment": f"Management Group {management_group} has been updated.",
        "name": management_group,
        "result": True,
    }
    ret = await hub.states.azurerm.managementgroup.operations.present(
        ctx, name=management_group, display_name=display_name,
    )
    assert ret == expected


@pytest.mark.run(order=-1)
@pytest.mark.asyncio
async def test_absent(hub, ctx, management_group):
    expected = {
        "changes": {"new": {}, "old": {"name": management_group,},},
        "comment": f"Management Group {management_group} has been deleted.",
        "name": management_group,
        "result": True,
    }
    ret = await hub.states.azurerm.managementgroup.operations.absent(
        ctx, management_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
