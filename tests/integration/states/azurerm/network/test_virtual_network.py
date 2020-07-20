import pytest


@pytest.fixture(scope="module")
def vnet_addr_prefixes():
    yield ["10.0.0.0/8"]


@pytest.fixture(scope="module")
def subnet_addr_prefix():
    yield "10.0.0.0/16"


@pytest.fixture(scope="module")
def changed_subnet_addr_prefix():
    yield "10.0.0.0/24"


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, test_vnet, resource_group, vnet_addr_prefixes):
    expected = {
        "changes": {
            "new": {
                "name": test_vnet,
                "resource_group": resource_group,
                "address_space": {"address_prefixes": vnet_addr_prefixes},
                "dhcp_options": {"dns_servers": None},
                "enable_ddos_protection": False,
                "enable_vm_protection": False,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Virtual network {test_vnet} has been created.",
        "name": test_vnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx,
        name=test_vnet,
        resource_group=resource_group,
        address_prefixes=vnet_addr_prefixes,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_subnet_present")
@pytest.mark.asyncio
async def test_changes(
    hub,
    ctx,
    test_vnet,
    resource_group,
    vnet_addr_prefixes,
    test_subnet,
    changed_subnet_addr_prefix,
):
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
        "comment": f"Virtual network {test_vnet} has been updated.",
        "name": test_vnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx,
        name=test_vnet,
        resource_group=resource_group,
        address_prefixes=changed_vnet_addr_prefixes,
    )
    assert ret == expected


@pytest.mark.run(after="test_changes", before="test_subnet_changes")
@pytest.mark.asyncio
async def test_subnet_present(
    hub, ctx, test_subnet, test_vnet, resource_group, subnet_addr_prefix
):
    expected = {
        "changes": {
            "new": {
                "name": test_subnet,
                "address_prefix": subnet_addr_prefix,
                "network_security_group": None,
                "route_table": None,
            },
            "old": {},
        },
        "comment": f"Subnet {test_subnet} has been created.",
        "name": test_subnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=test_subnet,
        virtual_network=test_vnet,
        resource_group=resource_group,
        address_prefix=subnet_addr_prefix,
    )
    assert ret == expected


@pytest.mark.run(after="test_subnet_present", before="test_subnet_absent")
@pytest.mark.asyncio
async def test_subnet_changes(
    hub,
    ctx,
    test_subnet,
    test_vnet,
    resource_group,
    subnet_addr_prefix,
    changed_subnet_addr_prefix,
):
    expected = {
        "changes": {
            "address_prefix": {
                "new": changed_subnet_addr_prefix,
                "old": subnet_addr_prefix,
            }
        },
        "comment": f"Subnet {test_subnet} has been updated.",
        "name": test_subnet,
        "result": True,
    }

    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=test_subnet,
        virtual_network=test_vnet,
        resource_group=resource_group,
        address_prefix=changed_subnet_addr_prefix,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_subnet_absent(hub, ctx, test_subnet, test_vnet, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": test_subnet,},},
        "comment": f"Subnet {test_subnet} has been deleted.",
        "name": test_subnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.subnet_absent(
        ctx, test_subnet, test_vnet, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, test_vnet, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": test_vnet,},},
        "comment": f"Virtual network {test_vnet} has been deleted.",
        "name": test_vnet,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, test_vnet, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
