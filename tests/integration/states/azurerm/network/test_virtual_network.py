import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, vnet, vnet2, resource_group):
    vnet_addr_prefixes = ["10.0.0.0/16"]
    expected = {
        "changes": {
            "new": {
                "name": vnet,
                "address_space": {"address_prefixes": vnet_addr_prefixes},
                "dhcp_options": {"dns_servers": []},
                "location": "eastus",
                "enable_ddos_protection": False,
                # "enable_vm_protection": False, # Not usable until next version bump
                "subnets": [],
                "virtual_network_peerings": [],
                "type": "Microsoft.Network/virtualNetworks",
                "provisioning_state": "Succeeded",
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
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    ret["changes"]["new"].pop("resource_guid")
    assert ret == expected

    # A second vnet is created here to be used in the vnet peering tests
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx,
        name=vnet2,
        resource_group=resource_group,
        address_prefixes=["172.0.0.0/8"],
    )
    assert ret["result"]


@pytest.mark.run(order=3, after="test_present", before="test_subnet_present")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, vnet, resource_group, subnet,
):
    vnet_addr_prefixes = ["10.0.0.0/16"]
    changed_vnet_addr_prefixes = ["10.0.0.0/16", "192.168.0.0/16", "128.0.0.0/16"]
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


# Tests the creation of a subnet with service endpoints, a GatewaySubnet, and a AzureBastionSubnet (all are necessary
# for other tests)
@pytest.mark.run(order=3, after="test_changes", before="test_subnet_changes")
@pytest.mark.asyncio
async def test_subnet_present(hub, ctx, subnet, vnet, resource_group):
    subnet_addr_prefix = "10.0.0.0/16"
    gateway_snet_addr_prefix = "192.168.0.0/16"
    bastion_snet_addr_prefix = "128.0.0.0/16"
    snet_expected = {
        "changes": {
            "new": {
                "name": subnet,
                "address_prefix": subnet_addr_prefix,
                "delegations": [],
                "provisioning_state": "Succeeded",
                "private_endpoint_network_policies": "Enabled",
                "private_link_service_network_policies": "Enabled",
                "service_endpoints": [
                    {
                        "service": "Microsoft.Sql",
                        "provisioning_state": "Succeeded",
                        "locations": ["eastus"],
                    }
                ],
            },
            "old": {},
        },
        "comment": f"Subnet {subnet} has been created.",
        "name": subnet,
        "result": True,
    }

    gateway_expected = {
        "changes": {
            "new": {
                "name": "GatewaySubnet",
                "address_prefix": gateway_snet_addr_prefix,
                "private_endpoint_network_policies": "Enabled",
                "private_link_service_network_policies": "Enabled",
                "provisioning_state": "Succeeded",
                "delegations": [],
            },
            "old": {},
        },
        "comment": f"Subnet GatewaySubnet has been created.",
        "name": "GatewaySubnet",
        "result": True,
    }

    bastion_expected = {
        "changes": {
            "new": {
                "name": "AzureBastionSubnet",
                "address_prefix": bastion_snet_addr_prefix,
                "private_endpoint_network_policies": "Enabled",
                "private_link_service_network_policies": "Enabled",
                "provisioning_state": "Succeeded",
                "delegations": [],
            },
            "old": {},
        },
        "comment": f"Subnet AzureBastionSubnet has been created.",
        "name": "AzureBastionSubnet",
        "result": True,
    }

    # Tests creation of a regular subnet with a service_endpoint
    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=subnet_addr_prefix,
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=["Microsoft.Sql"],
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    assert ret == snet_expected

    # Tests creation of a GatewaySubnet used by a virtual network gateway
    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name="GatewaySubnet",
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=gateway_snet_addr_prefix,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    assert ret == gateway_expected

    # Tests creation of an AzureBastionSubnet used by a Bastion Host
    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name="AzureBastionSubnet",
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=bastion_snet_addr_prefix,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    assert ret == bastion_expected


@pytest.mark.run(order=3, after="test_subnet_present", before="test_subnet_absent")
@pytest.mark.asyncio
async def test_subnet_changes(
    hub, ctx, subnet, vnet, resource_group,
):
    subnet_addr_prefix = "10.0.0.0/16"
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
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=["Microsoft.Sql"],
    )
    assert ret == expected


@pytest.mark.run(order=-3, before="test_absent")
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


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, vnet, vnet2, resource_group):
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

    # The second vnet used by the vnet peering tests is removed here
    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, name=vnet2, resource_group=resource_group,
    )
    assert ret["result"]
