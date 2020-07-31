import pytest
import random
import string


@pytest.fixture(scope="session")
def vnet_peering():
    yield "vnet-peering-idem" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, vnet_peering, resource_group, vnet, vnet2):
    expected = {
        "changes": {
            "new": {
                "name": vnet_peering,
                "remote_virtual_network": vnet2,
                "remote_vnet_group": resource_group,
                "allow_virtual_network_access": True,
                "allow_forwarded_traffic": False,
                "allow_gateway_transit": False,
                "use_remote_gateways": False,
            },
            "old": {},
        },
        "comment": f"Peering object {vnet_peering} has been created.",
        "name": vnet_peering,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_peering.present(
        ctx,
        name=vnet_peering,
        resource_group=resource_group,
        virtual_network=vnet,
        remote_virtual_network=vnet2,
        remote_vnet_group=resource_group,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, vnet_peering, resource_group, vnet, vnet2):
    expected = {
        "changes": {"allow_forwarded_traffic": {"new": True, "old": False}},
        "comment": f"Peering object {vnet_peering} has been updated.",
        "name": vnet_peering,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_peering.present(
        ctx,
        name=vnet_peering,
        resource_group=resource_group,
        virtual_network=vnet,
        remote_virtual_network=vnet2,
        remote_vnet_group=resource_group,
        allow_forwarded_traffic=True,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, vnet_peering, vnet, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": vnet_peering,},},
        "comment": f"Peering object {vnet_peering} has been deleted.",
        "name": vnet_peering,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_peering.absent(
        ctx, name=vnet_peering, virtual_network=vnet, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
