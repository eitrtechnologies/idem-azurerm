import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, load_balancer, resource_group):
    sku = "Basic"
    expected = {
        "changes": {
            "new": {
                "name": load_balancer,
                "location": "eastus",
                "sku": {"name": sku},
                "frontend_ip_configurations": [],
                "backend_address_pools": [],
                "load_balancing_rules": [],
                "probes": [],
                "inbound_nat_rules": [],
                "inbound_nat_pools": [],
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/loadBalancers",
            },
            "old": {},
        },
        "comment": f"Load balancer {load_balancer} has been created.",
        "name": load_balancer,
        "result": True,
    }
    ret = await hub.states.azurerm.network.load_balancer.present(
        ctx, name=load_balancer, resource_group=resource_group, sku=sku
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("etag")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, load_balancer, resource_group, tags):
    sku = "Basic"
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Load balancer {load_balancer} has been updated.",
        "name": load_balancer,
        "result": True,
    }
    ret = await hub.states.azurerm.network.load_balancer.present(
        ctx, name=load_balancer, resource_group=resource_group, sku=sku, tags=tags
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, load_balancer, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": load_balancer,},},
        "comment": f"Load balancer {load_balancer} has been deleted.",
        "name": load_balancer,
        "result": True,
    }
    ret = await hub.states.azurerm.network.load_balancer.absent(
        ctx, load_balancer, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
