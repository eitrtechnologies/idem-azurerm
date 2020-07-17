import pytest
import string
import random


@pytest.fixture(scope="session")
def ip_config():
    yield "idem-ip-config-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=2)
@pytest.mark.asyncio
# This setup function deploys the following to use within tests:
# - Virtual Network
# - Subnet
# - Network Interface
async def test_setup(
    hub, ctx, vnet, subnet, network_interface, resource_group, ip_config
):
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

    ret = await hub.states.azurerm.network.network_interface.present(
        ctx,
        name=network_interface,
        resource_group=resource_group,
        subnet=subnet,
        virtual_network=vnet,
        ip_configurations=[{"name": ip_config}],
    )


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_teardown(hub, ctx, vnet, subnet, network_interface, resource_group):
    ret = await hub.states.azurerm.network.network_interface.absent(
        ctx, name=network_interface, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.subnet_absent(
        ctx, name=subnet, virtual_network=vnet, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, name=vnet, resource_group=resource_group
    )
    assert ret["result"] == True
