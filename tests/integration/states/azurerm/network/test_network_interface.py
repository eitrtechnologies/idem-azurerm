import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, network_interface, subnet, vnet, resource_group, ip_config
):
    expected = {
        "changes": {
            "new": {
                "name": network_interface,
                "ip_configurations": [
                    {
                        "name": ip_config,
                        "primary": True,
                        "private_ip_address": "10.0.0.4",
                        "private_ip_address_version": "IPv4",
                        "private_ip_allocation_method": "Dynamic",
                        "provisioning_state": "Succeeded",
                    },
                ],
                "dns_settings": {"applied_dns_servers": [], "dns_servers": []},
                "enable_accelerated_networking": False,
                "enable_ip_forwarding": False,
                "type": "Microsoft.Network/networkInterfaces",
                "tap_configurations": [],
                "location": "eastus",
                "provisioning_state": "Succeeded",
                "hosted_workloads": [],
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
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("etag")
    ret["changes"]["new"]["ip_configurations"][0].pop("etag")
    ret["changes"]["new"]["ip_configurations"][0].pop("id")
    ret["changes"]["new"]["ip_configurations"][0].pop("subnet")
    ret["changes"]["new"]["dns_settings"].pop("internal_domain_name_suffix")
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
        "changes": {
            "new": {},
            "old": {
                "name": network_interface,
            },
        },
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
