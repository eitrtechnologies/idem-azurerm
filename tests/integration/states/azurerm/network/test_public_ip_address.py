import pytest


@pytest.fixture(scope="module")
def idle_timeout():
    yield 10


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, test_public_ip_addr, resource_group, idle_timeout):
    expected = {
        "changes": {
            "new": {
                "name": test_public_ip_addr,
                "tags": None,
                "dns_settings": None,
                "sku": None,
                "public_ip_allocation_method": None,
                "public_ip_address_version": None,
                "idle_timeout_in_minutes": idle_timeout,
            },
            "old": {},
        },
        "comment": f"Public IP address {test_public_ip_addr} has been created.",
        "name": test_public_ip_addr,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_address.present(
        ctx,
        name=test_public_ip_addr,
        resource_group=resource_group,
        idle_timeout_in_minutes=idle_timeout,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, test_public_ip_addr, resource_group, idle_timeout):
    new_timeout = 4
    expected = {
        "changes": {
            "idle_timeout_in_minutes": {"new": new_timeout, "old": idle_timeout}
        },
        "comment": f"Public IP address {test_public_ip_addr} has been updated.",
        "name": test_public_ip_addr,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_address.present(
        ctx,
        name=test_public_ip_addr,
        resource_group=resource_group,
        idle_timeout_in_minutes=new_timeout,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, test_public_ip_addr, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": test_public_ip_addr,},},
        "comment": f"Public IP address {test_public_ip_addr} has been deleted.",
        "name": test_public_ip_addr,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_address.absent(
        ctx, test_public_ip_addr, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
