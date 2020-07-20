import pytest
import string
import random


@pytest.fixture(scope="session")
def local_network_gateway():
    yield "idem-local-net-gateway-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="module")
def gateway_ip_addr():
    yield "192.168.0.1"


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, local_network_gateway, resource_group, gateway_ip_addr
):
    expected = {
        "changes": {
            "new": {
                "name": local_network_gateway,
                "resource_group": resource_group,
                "gateway_ip_address": gateway_ip_addr,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Local network gateway {local_network_gateway} has been created.",
        "name": local_network_gateway,
        "result": True,
    }
    ret = await hub.states.azurerm.network.local_network_gateway.present(
        ctx,
        name=local_network_gateway,
        resource_group=resource_group,
        gateway_ip_address=gateway_ip_addr,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, local_network_gateway, resource_group, gateway_ip_addr
):
    addr_prefixes = ["10.0.0.0/8"]
    expected = {
        "changes": {
            "local_network_address_space": {
                "address_prefixes": {"new": addr_prefixes, "old": []}
            }
        },
        "comment": f"Local network gateway {local_network_gateway} has been updated.",
        "name": local_network_gateway,
        "result": True,
    }
    ret = await hub.states.azurerm.network.local_network_gateway.present(
        ctx,
        name=local_network_gateway,
        resource_group=resource_group,
        gateway_ip_address=gateway_ip_addr,
        address_prefixes=addr_prefixes,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, local_network_gateway, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": local_network_gateway,},},
        "comment": f"Local network gateway {local_network_gateway} has been deleted.",
        "name": local_network_gateway,
        "result": True,
    }
    ret = await hub.states.azurerm.network.local_network_gateway.absent(
        ctx, name=local_network_gateway, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
