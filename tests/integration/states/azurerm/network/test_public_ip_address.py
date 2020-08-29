import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, public_ip_addr, resource_group):
    idle_timeout = 10
    expected = {
        "changes": {
            "new": {
                "name": public_ip_addr,
                "resource_group": resource_group,
                "sku": {"name": "Standard"},
                "tags": None,
                "public_ip_allocation_method": "Static",
                "public_ip_address_version": None,
                "idle_timeout_in_minutes": idle_timeout,
            },
            "old": {},
        },
        "comment": f"Public IP address {public_ip_addr} has been created.",
        "name": public_ip_addr,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_address.present(
        ctx,
        name=public_ip_addr,
        resource_group=resource_group,
        public_ip_allocation_method="Static",
        sku="Standard",
        idle_timeout_in_minutes=idle_timeout,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, public_ip_addr, resource_group, tags):
    idle_timeout = 10
    new_timeout = 4
    expected = {
        "changes": {
            "idle_timeout_in_minutes": {"new": new_timeout, "old": idle_timeout},
            "tags": {"new": tags},
        },
        "comment": f"Public IP address {public_ip_addr} has been updated.",
        "name": public_ip_addr,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_address.present(
        ctx,
        name=public_ip_addr,
        resource_group=resource_group,
        sku="Standard",
        public_ip_allocation_method="Static",
        idle_timeout_in_minutes=new_timeout,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, public_ip_addr, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": public_ip_addr,},},
        "comment": f"Public IP address {public_ip_addr} has been deleted.",
        "name": public_ip_addr,
        "result": True,
    }
    ret = await hub.states.azurerm.network.public_ip_address.absent(
        ctx, public_ip_addr, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
