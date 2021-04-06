import pytest
import random
import string


@pytest.fixture(scope="session")
def host_group():
    yield "host-group-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_present(hub, ctx, host_group, resource_group, location):
    expected = {
        "changes": {
            "new": {
                "name": host_group,
                "location": location,
                "platform_fault_domain_count": 2,
                "support_automatic_placement": False,
                "type": "Microsoft.Compute/hostGroups",
            },
            "old": {},
        },
        "comment": f"Dedicated host group {host_group} has been created.",
        "name": host_group,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.dedicated_host_group.present(
        ctx,
        name=host_group,
        resource_group=resource_group,
        platform_fault_domain_count=2,
    )
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=2, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, host_group, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Dedicated host group {host_group} has been updated.",
        "name": host_group,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.dedicated_host_group.present(
        ctx,
        name=host_group,
        resource_group=resource_group,
        platform_fault_domain_count=2,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_absent(hub, ctx, host_group, resource_group):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": host_group,
            },
        },
        "comment": f"SSH public key {host_group} has been deleted.",
        "name": host_group,
        "result": True,
    }
    ret = await hub.states.azurerm.compute.dedicated_host_group.absent(
        ctx, host_group, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
