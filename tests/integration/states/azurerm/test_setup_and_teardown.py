import pytest
import string
import random


@pytest.mark.run(order=2)
@pytest.mark.asyncio
# This setup function deploys the following to use within tests:
# - 2 Virtual Networks
# - 1 Subnet
async def test_setup(
    hub, ctx, vnet, vnet2, subnet, resource_group,
):
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx, name=vnet, resource_group=resource_group, address_prefixes=["172.0.0.0/8"],
    )
    assert ret["result"]

    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx, name=vnet2, resource_group=resource_group, address_prefixes=["10.0.0.0/8"],
    )
    assert ret["result"]

    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix="172.0.0.0/16",
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=[{"service": "Microsoft.sql"}],
    )
    assert ret["result"]

    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name="GatewaySubnet",
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix="172.17.1.0/24",
    )
    assert ret["result"]


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_teardown(
    hub, ctx, vnet, vnet2, subnet, resource_group,
):

    ret = await hub.states.azurerm.network.virtual_network.subnet_absent(
        ctx, name=subnet, virtual_network=vnet, resource_group=resource_group
    )
    assert ret["result"]

    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, name=vnet, resource_group=resource_group
    )
    assert ret["result"]

    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, name=vnet2, resource_group=resource_group
    )
    assert ret["result"]
