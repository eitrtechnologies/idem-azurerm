import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, network_interface, subnet, vnet, resource_group, ip_config
):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"

    expected = {
        "changes": {
            "new": {
                "name": network_interface,
                "tags": None,
                "ip_configurations": [
                    {"name": ip_config, "subnet": {"id": subnet_id},}
                ],
                "dns_settings": None,
                "network_security_group": None,
                "enable_accelerated_networking": None,
                "enable_ip_forwarding": None,
            },
            "old": {},
        },
        "comment": f"Network interface {network_interface} has been created.",
        "name": network_interface,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_interface.present(
        ctx,
        name=network_interface,
        subnet=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        ip_configurations=[{"name": ip_config}],
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, network_interface, subnet, vnet, resource_group, ip_config, tags
):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Network interface {network_interface} has been updated.",
        "name": network_interface,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_interface.present(
        ctx,
        name=network_interface,
        subnet=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        ip_configurations=[{"name": ip_config}],
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, network_interface, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": network_interface,},},
        "comment": f"Network interface {network_interface} has been deleted.",
        "name": network_interface,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_interface.absent(
        ctx, name=network_interface, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
