import pytest
import random
import string


@pytest.fixture(scope="session")
def vnet_gateway():
    yield "vgw-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def vnet_gateway_connection():
    yield "vgw-connection-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="module")
def ipsec_policy():
    yield {
        "sa_life_time_seconds": 300,
        "sa_data_size_kilobytes": 1024,
        "ipsec_encryption": "DES",
        "ipsec_integrity": "SHA256",
        "ike_encryption": "DES",
        "ike_integrity": "SHA256",
        "dh_group": "None",
        "pfs_group": "None",
    }


@pytest.mark.run(order=4)
@pytest.mark.slow
@pytest.mark.asyncio
async def test_present(
    hub, ctx, vnet_gateway, resource_group, ip_config, public_ip_addr2, vnet,
):
    gateway_type = "Vpn"
    vpn_type = "RouteBased"
    sku = "VpnGw1"
    configs = [
        {
            "name": ip_config,
            "public_ip_address": public_ip_addr2,
            "private_ip_allocation_method": "Dynamic",
        }
    ]
    active_active = False
    enable_bgp = False
    expected = {
        "changes": {
            "new": {
                "name": vnet_gateway,
                "resource_group": resource_group,
                "virtual_network": vnet,
                "ip_configurations": configs,
                "gateway_type": gateway_type,
                "enable_bgp": enable_bgp,
                "active_active": active_active,
                "vpn_type": vpn_type,
                "sku": {"name": sku, "tier": sku},
            },
            "old": {},
        },
        "comment": f"Virtual network gateway {vnet_gateway} has been created.",
        "name": vnet_gateway,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_gateway.present(
        ctx,
        name=vnet_gateway,
        resource_group=resource_group,
        virtual_network=vnet,
        ip_configurations=configs,
        gateway_type=gateway_type,
        enable_bgp=enable_bgp,
        active_active=active_active,
        vpn_type=vpn_type,
        sku=sku,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.slow
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, vnet_gateway, resource_group, ip_config, public_ip_addr2, vnet, tags,
):
    gateway_type = "Vpn"
    vpn_type = "RouteBased"
    sku = "VpnGw1"
    configs = [
        {
            "name": ip_config,
            "public_ip_address": public_ip_addr2,
            "private_ip_allocation_method": "Dynamic",
        }
    ]
    active_active = False
    enable_bgp = False
    expected = {
        "changes": {"tags": {"new": tags,}},
        "comment": f"Virtual network gateway {vnet_gateway} has been updated.",
        "name": vnet_gateway,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_gateway.present(
        ctx,
        name=vnet_gateway,
        resource_group=resource_group,
        virtual_network=vnet,
        ip_configurations=configs,
        gateway_type=gateway_type,
        enable_bgp=enable_bgp,
        active_active=active_active,
        vpn_type=vpn_type,
        tags=tags,
        sku=sku,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_changes", before="test_connection_changes")
@pytest.mark.slow
@pytest.mark.asyncio
async def test_connection_present(
    hub,
    ctx,
    vnet_gateway_connection,
    vnet_gateway,
    resource_group,
    local_network_gateway,
    ipsec_policy,
):
    connection_type = "IPSec"
    use_selectors = True
    shared_key = "sharedKey"
    enable_bgp = False

    expected = {
        "changes": {
            "new": {
                "name": vnet_gateway_connection,
                "resource_group": resource_group,
                "virtual_network_gateway": vnet_gateway,
                "connection_type": connection_type,
                "local_network_gateway2": local_network_gateway,
                "enable_bgp": enable_bgp,
                "shared_key": "REDACTED",
                "use_policy_based_traffic_selectors": use_selectors,
                "ipsec_policies": [ipsec_policy],
            },
            "old": {},
        },
        "comment": f"Virtual network gateway connection {vnet_gateway_connection} has been created.",
        "name": vnet_gateway_connection,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_gateway.connection_present(
        ctx,
        name=vnet_gateway_connection,
        virtual_network_gateway=vnet_gateway,
        resource_group=resource_group,
        local_network_gateway2=local_network_gateway,
        connection_type=connection_type,
        enable_bgp=enable_bgp,
        shared_key=shared_key,
        use_policy_based_traffic_selectors=use_selectors,
        ipsec_policy=ipsec_policy,
    )
    assert ret == expected


@pytest.mark.run(
    order=4, after="test_connection_present", before="test_connection_absent"
)
@pytest.mark.slow
@pytest.mark.asyncio
async def test_connection_changes(
    hub,
    ctx,
    vnet_gateway_connection,
    vnet_gateway,
    resource_group,
    local_network_gateway,
    ipsec_policy,
    tags,
):
    connection_type = "IPSec"
    updated_key = "updatedKey"
    use_selectors = True
    enable_bgp = False
    expected = {
        "changes": {"shared_key": {"new": "REDACTED"}, "tags": {"new": tags}},
        "comment": f"Virtual network gateway connection {vnet_gateway_connection} has been updated.",
        "name": vnet_gateway_connection,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_gateway.connection_present(
        ctx,
        name=vnet_gateway_connection,
        virtual_network_gateway=vnet_gateway,
        resource_group=resource_group,
        local_network_gateway2=local_network_gateway,
        connection_type=connection_type,
        enable_bgp=enable_bgp,
        shared_key=updated_key,
        use_policy_based_traffic_selectors=use_selectors,
        ipsec_policy=ipsec_policy,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-4, before="test_absent")
@pytest.mark.slow
@pytest.mark.asyncio
async def test_connection_absent(hub, ctx, vnet_gateway_connection, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": vnet_gateway_connection,},},
        "comment": f"Virtual network gateway connection {vnet_gateway_connection} has been deleted.",
        "name": vnet_gateway_connection,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_gateway.connection_absent(
        ctx, name=vnet_gateway_connection, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=-4)
@pytest.mark.slow
@pytest.mark.asyncio
async def test_absent(hub, ctx, vnet_gateway, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": vnet_gateway,},},
        "comment": f"Virtual network gateway {vnet_gateway} has been deleted.",
        "name": vnet_gateway,
        "result": True,
    }
    ret = await hub.states.azurerm.network.virtual_network_gateway.absent(
        ctx, name=vnet_gateway, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
