import pytest


@pytest.mark.asyncio
async def test_absent_present(hub, subtests):
    ctx = {"acct": {}, "test": False}
    ret = await hub.states.azurerm.resource.group.absent(ctx, "name")
    assert ret == {"actual result": "value"}

    with subtests.test(action="present"):
        ret = await hub.states.azurerm.resource.group.present(ctx, "name")
        assert ret == {"actual result": "value"}

    ret = await hub.states.azurerm.resource.group.absent(ctx, "name")
    assert ret == {"actual result": "value"}
