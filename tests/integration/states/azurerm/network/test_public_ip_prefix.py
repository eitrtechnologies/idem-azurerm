import pytest
import random
import string


@pytest.fixture(scope="session")
def public_ip_prefix():
    yield "ip-prefix-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, public_ip_prefix, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": public_ip_prefix,
                "sku": {"name": "Standard"},
                "public_ip_address_version": "IPv4",
                "prefix_length": 31,
                "ip_tags": [],
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/publicIPPrefixes",
                "location": "eastus",
            },
            "old": {},
        },
        "comment": f"Public IP prefix {public_ip_prefix} has been created.",
        "name": public_ip_prefix,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_prefix.present(
        ctx, name=public_ip_prefix, resource_group=resource_group, prefix_length=31
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("ip_prefix")
    ret["changes"]["new"].pop("etag")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, public_ip_prefix, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags},},
        "comment": f"Public IP prefix {public_ip_prefix} has been updated.",
        "name": public_ip_prefix,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_prefix.present(
        ctx,
        name=public_ip_prefix,
        resource_group=resource_group,
        prefix_length=31,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, public_ip_prefix, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": public_ip_prefix,},},
        "comment": f"Public IP prefix {public_ip_prefix} has been deleted.",
        "name": public_ip_prefix,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_prefix.absent(
        ctx, public_ip_prefix, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
