import pytest


@pytest.fixture(scope="module")
def vnet_addr_prefixes():
    yield ["10.0.0.0/8"]


@pytest.fixture(scope="module")
def subnet_addr_prefix():
    yield "10.0.0.0/16"


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_vnet_present(hub, ctx, vnet, resource_group, vnet_addr_prefixes):
    expected = {
        "changes": {
            "new": {
                "name": vnet,
                "resource_group": resource_group,
                "address_space": {"address_prefixes": vnet_addr_prefixes},
                "dhcp_options": {"dns_servers": None},
                "enable_ddos_protection": False,
                "enable_vm_protection": False,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Virtual network {vnet} has been created.",
        "name": vnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx,
        name=vnet,
        resource_group=resource_group,
        address_prefixes=vnet_addr_prefixes,
    )
    assert ret == expected


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_subnet_present(
    hub, ctx, subnet, vnet, resource_group, subnet_addr_prefix
):
    expected = {
        "changes": {
            "new": {
                "name": subnet,
                "address_prefix": subnet_addr_prefix,
                "network_security_group": None,
                "route_table": None,
            },
            "old": {},
        },
        "comment": f"Subnet {subnet} has been created.",
        "name": subnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=subnet_addr_prefix,
    )
    assert ret == expected


@pytest.mark.run(after="test_vnet_present", before="test_vnet_absent")
@pytest.mark.asyncio
async def test_vnet_changes(hub, ctx, vnet, resource_group, vnet_addr_prefixes):
    changed_vnet_addr_prefixes = ["10.0.0.0/8", "192.168.0.0/16"]
    expected = {
        "changes": {
            "address_space": {
                "address_prefixes": {
                    "new": changed_vnet_addr_prefixes,
                    "old": vnet_addr_prefixes,
                }
            }
        },
        "comment": f"Virtual network {vnet} has been updated.",
        "name": vnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx,
        name=vnet,
        resource_group=resource_group,
        address_prefixes=changed_vnet_addr_prefixes,
    )
    assert ret == expected


@pytest.mark.run(after="test_subnet_present", before="test_subnet_absent")
@pytest.mark.asyncio
async def test_subnet_changes(
    hub, ctx, subnet, vnet, resource_group, subnet_addr_prefix
):
    changed_subnet_addr_prefix = "10.0.0.0/24"
    expected = {
        "changes": {
            "address_prefix": {
                "new": changed_subnet_addr_prefix,
                "old": subnet_addr_prefix,
            }
        },
        "comment": f"Subnet {subnet} has been updated.",
        "name": subnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=changed_subnet_addr_prefix,
    )
    assert ret == expected


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_vnet_absent(hub, ctx, vnet, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": vnet,},},
        "comment": f"Virtual network {vnet} has been deleted.",
        "name": vnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, vnet, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_subnet_absent(hub, ctx, subnet, vnet, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": subnet,},},
        "comment": f"Subnet {subnet} has been deleted.",
        "name": subnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.subnet_absent(
        ctx, subnet, vnet, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
