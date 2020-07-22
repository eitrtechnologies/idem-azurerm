import pytest
import string
import random


@pytest.fixture(scope="session")
def vnet_gateway():
    yield "idem-vnet-gateway-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def vnet_gateway_connection():
    yield "idem-vnet-gateway-connection-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="module")
def gateway_type():
    yield "Vpn"


@pytest.fixture(scope="module")
def active_active():
    yield False


@pytest.fixture(scope="module")
def enable_bgp():
    yield False


@pytest.fixture(scope="module")
def vpn_type():
    yield "RouteBased"


@pytest.fixture(scope="module")
def connection_type():
    yield "IPSec"


@pytest.fixture(scope="module")
def shared_key():
    yield "sharedKey"


@pytest.fixture(scope="module")
def use_selectors():
    yield True


@pytest.fixture(scope="module")
def ipsec_policies():
    yield [
        {
            "sa_life_time_seconds": 300,
            "sa_data_size_kilobytes": 1024,
            "ipsec_encryption": "DES",
            "ipsec_integrity": "SHA256",
            "ike_encryption": "DES",
            "ike_integrity": "SHA256",
            "dh_group": "None",
            "pfs_group": "None",
        }
    ]


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub,
    ctx,
    vnet_gateway,
    resource_group,
    ip_config,
    public_ip_addr,
    vnet,
    gateway_type,
    active_active,
    enable_bgp,
    vpn_type,
):
    configs = [
        {
            "name": ip_config,
            "public_ip_address": public_ip_addr,
            "private_ip_allocation_method": "Dynamic",
        }
    ]
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
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub,
    ctx,
    vnet_gateway,
    resource_group,
    ip_config,
    public_ip_addr,
    vnet,
    gateway_type,
    active_active,
    enable_bgp,
    vpn_type,
    tags,
):
    configs = [
        {
            "name": ip_config,
            "public_ip_address": public_ip_addr,
            "private_ip_allocation_method": "Dynamic",
        }
    ]
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
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_changes", before="test_connection_changes")
@pytest.mark.asyncio
async def test_connection_present(
    hub,
    ctx,
    vnet_gateway_connection,
    vnet_gateway,
    resource_group,
    local_network_gateway,
    connection_type,
    enable_bgp,
    shared_key,
    use_selectors,
    ipsec_policies,
):
    expected = {
        "changes": {
            "new": {
                "name": vnet_gateway_connection,
                "resource_group": resource_group,
                "virtual_network_gateway": vnet_gateway,
                "connection_type": connection_type,
                "local_network_gateway2": local_network_gateway,
                "enable_bgp": enable_bgp,
                "shared_key": shared_key,
                "use_policy_based_traffic_selectors": use_selectors,
                "ipsec_policies": ipsec_policies,
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
        ipsec_policies=ipsec_policies,
    )
    assert ret == expected


@pytest.mark.run(
    order=4, after="test_connection_present", before="test_connection_absent"
)
@pytest.mark.asyncio
async def test_connection_changes(
    hub,
    ctx,
    vnet_gateway_connection,
    vnet_gateway,
    resource_group,
    local_network_gateway,
    connection_type,
    enable_bgp,
    shared_key,
    use_selectors,
    ipsec_policies,
):
    updated_key = "updatedKey"
    expected = {
        "changes": {"shared_key": {"new": "REDACTED"}},
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
        ipsec_policies=ipsec_policies,
    )
    assert ret == expected


@pytest.mark.run(order=-4, before="test_absent")
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
