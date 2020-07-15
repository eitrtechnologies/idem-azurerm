import pytest


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_table_present(hub, ctx, route_table, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": route_table,
                "tags": None,
                "routes": None,
                "disable_bgp_route_propagation": None,
            },
            "old": {},
        },
        "comment": f"Route table {route_table} has been created.",
        "name": route_table,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.table_present(
        ctx, name=route_table, resource_group=resource_group,
    )
    assert ret == expected


@pytest.mark.run(after="test_table_present", before="test_table_absent")
@pytest.mark.asyncio
async def test_table_changes(hub, ctx, route_table, resource_group):
    routes = [
        {
            "name": "test_route1",
            "address_prefix": "0.0.0.0/0",
            "next_hop_type": "internet",
        }
    ]
    expected = {
        "changes": {"routes": {"new": routes, "old": []}},
        "comment": f"Route table {route_table} has been updated.",
        "name": route_table,
        "result": True,
    }
    ret = await hub.states.azurerm.network.route.table_present(
        ctx, name=route_table, resource_group=resource_group, routes=routes,
    )
    assert ret == expected


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
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
