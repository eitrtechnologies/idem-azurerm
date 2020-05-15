import pytest


# Option 1
@pytest.fixture
def hub(hub):
    # Setup
    ret = await hub.states.azurerm.resource.group.absent("name")
    assert ret == {"actual result": "value"}

    yield hub

    # Teardown
    ret = await hub.states.azurerm.resource.group.absent("name")
    assert ret == {"actual result": "value"}


@pytest.mark.asyncio
async def test_present(hub):
    ret = await hub.states.azurerm.resource.group.present("name")
    assert ret == {"actual result": "value"}


# /option 1

# option 2
@pytest.mark.asyncio
async def test_absent_present(hub, subtests):
    ret = await hub.states.azurerm.resource.group.absent("name")
    assert ret == {"actual result": "value"}

    with subtests.test(action="present"):
        ret = await hub.states.azurerm.resource.group.present("name")
        assert ret == {"actual result": "value"}

    ret = await hub.states.azurerm.resource.group.absent("name")
    assert ret == {"actual result": "value"}
# /option 2
