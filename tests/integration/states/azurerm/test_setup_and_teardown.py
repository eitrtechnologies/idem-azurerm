import pytest


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_setup(hub, ctx, vnet, subnet, resource_group):
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx, name=vnet, resource_group=resource_group, address_prefixes=["172.0.0.0/8"],
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix="172.0.0.0/16",
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=[{"service": "Microsoft.sql"}],
    )
    assert ret["result"] == True


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_teardown(hub, ctx, vnet, subnet, resource_group):
    ret = await hub.states.azurerm.network.virtual_network.subnet_absent(
        ctx, subnet, vnet, resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, vnet, resource_group
    )
    assert ret["result"] == True
