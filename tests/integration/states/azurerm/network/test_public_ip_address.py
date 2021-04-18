import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
# Creates a public IP address with a "Standard" SKU for Bastion Host tests and another one with a "Basic" SKU
# for the virtual network gateway tests
async def test_present(hub, ctx, public_ip_addr, public_ip_addr2, resource_group):
    idle_timeout = 10
    standard_expected = {
        "changes": {
            "new": {
                "name": public_ip_addr,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
                "public_ip_address_version": "IPv4",
                "idle_timeout_in_minutes": idle_timeout,
                "type": "Microsoft.Network/publicIPAddresses",
                "provisioning_state": "Succeeded",
                "location": "eastus",
                "ip_tags": [],
            },
            "old": {},
        },
        "comment": f"Public IP address {public_ip_addr} has been created.",
        "name": public_ip_addr,
        "result": True,
    }

    basic_expected = {
        "changes": {
            "new": {
                "name": public_ip_addr2,
                "sku": {"name": "Basic"},
                "public_ip_allocation_method": "Dynamic",
                "public_ip_address_version": "IPv4",
                "idle_timeout_in_minutes": idle_timeout,
                "type": "Microsoft.Network/publicIPAddresses",
                "provisioning_state": "Succeeded",
                "location": "eastus",
                "ip_tags": [],
            },
            "old": {},
        },
        "comment": f"Public IP address {public_ip_addr2} has been created.",
        "name": public_ip_addr2,
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
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("ip_address")
    ret["changes"]["new"].pop("etag")
    assert ret == standard_expected

    ret = await hub.states.azurerm.network.public_ip_address.present(
        ctx,
        name=public_ip_addr2,
        resource_group=resource_group,
        sku="Basic",
        idle_timeout_in_minutes=idle_timeout,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("etag")
    assert ret == basic_expected


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
        "changes": {
            "new": {},
            "old": {
                "name": public_ip_addr,
            },
        },
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
