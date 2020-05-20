import pytest


@pytest.mark.run(before="test_absent")
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location):
    ret = await hub.states.azurerm.resource.group.present(ctx, resource_group, location)
    assert ret == {"actual result": "value"}


@pytest.mark.run(after="test_present")
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group):
    ret = await hub.states.azurerm.resource.group.absent(ctx, resource_group)
    assert ret == {"actual result": "value"}
