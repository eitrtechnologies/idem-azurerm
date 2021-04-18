import pytest
import random
import string


@pytest.fixture(scope="session")
def ssh_key():
    yield "ssh-key-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_present(hub, ctx, ssh_key, resource_group, location):
    expected = {
        "changes": {"new": {"name": ssh_key, "location": location,}, "old": {},},
        "comment": f"SSH public key {ssh_key} has been created.",
        "name": ssh_key,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.ssh_public_key.present(
        ctx, name=ssh_key, resource_group=resource_group
    )
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=2, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, ssh_key, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"SSH public key {ssh_key} has been updated.",
        "name": ssh_key,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.ssh_public_key.present(
        ctx, name=ssh_key, resource_group=resource_group, tags=tags
    )
    assert ret == expected


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_absent(hub, ctx, ssh_key, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": ssh_key,},},
        "comment": f"SSH public key {ssh_key} has been deleted.",
        "name": ssh_key,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.ssh_public_key.absent(
        ctx, ssh_key, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
