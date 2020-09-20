import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_table_present(hub, ctx, route_table, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": route_table,
                "routes": [],
                "disable_bgp_route_propagation": False,
                "location": "eastus",
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/routeTables",
            },
            "old": {},
        },
        "comment": f"Route table {route_table} has been created.",
        "name": route_table,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.table_present(
        ctx, name=route_table, resource_group=resource_group
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    assert ret == expected


@pytest.mark.run(order=3, after="test_table_present", before="test_present")
@pytest.mark.asyncio
async def test_table_changes(hub, ctx, route_table, resource_group, route, tags):
    new_routes = [
        {
            "name": "test_route1",
            "address_prefix": "0.0.0.0/0",
            "next_hop_type": "internet",
        }
    ]

    expected = {
        "changes": {"routes": {"new": new_routes, "old": []}, "tags": {"new": tags}},
        "comment": f"Route table {route_table} has been updated.",
        "name": route_table,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.table_present(
        ctx,
        name=route_table,
        resource_group=resource_group,
        routes=new_routes,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_table_changes", before="test_changes")
@pytest.mark.asyncio
async def test_present(hub, ctx, route, route_table, resource_group):
    next_hop_type = "vnetlocal"
    addr_prefix = "192.168.0.0/16"
    expected = {
        "changes": {
            "new": {
                "name": route,
                "address_prefix": addr_prefix,
                "next_hop_type": "VnetLocal",
                "provisioning_state": "Succeeded",
            },
            "old": {},
        },
        "comment": f"Route {route} has been created.",
        "name": route,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.present(
        ctx,
        name=route,
        route_table=route_table,
        resource_group=resource_group,
        address_prefix=addr_prefix,
        next_hop_type=next_hop_type,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, route, route_table, resource_group,
):
    next_hop_type = "vnetlocal"
    addr_prefix = "192.168.0.0/16"
    changed_addr_prefix = "192.168.0.0/24"
    expected = {
        "changes": {"address_prefix": {"new": changed_addr_prefix, "old": addr_prefix}},
        "comment": f"Route {route} has been updated.",
        "name": route,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.present(
        ctx,
        name=route,
        route_table=route_table,
        resource_group=resource_group,
        address_prefix=changed_addr_prefix,
        next_hop_type=next_hop_type,
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_table_changes", before="test_table_absent")
@pytest.mark.asyncio
async def test_absent(hub, ctx, route, route_table, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": route,},},
        "comment": f"Route {route} has been deleted.",
        "name": route,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.absent(
        ctx, route, route_table, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.asyncio
@pytest.mark.run(order=-3)
async def test_table_absent(hub, ctx, route_table, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": route_table,},},
        "comment": f"Route table {route_table} has been deleted.",
        "name": route_table,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.table_absent(
        ctx, route_table, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
