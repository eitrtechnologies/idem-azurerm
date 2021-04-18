import pytest
import random
import string


@pytest.fixture(scope="session")
def vnet_rule():
    yield "psql-vnet-rule-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, vnet_rule, postgresql_server, resource_group, subnet, vnet,
):
    ignore_missing_endpoint = False
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"
    expected = {
        "changes": {
            "new": {
                "name": vnet_rule,
                "state": "Ready",
                "ignore_missing_vnet_service_endpoint": ignore_missing_endpoint,
                "type": "Microsoft.DBforPostgreSQL/servers/virtualNetworkRules",
            },
            "old": {},
        },
        "comment": f"Virtual Network Rule {vnet_rule} has been created.",
        "name": vnet_rule,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.virtual_network_rule.present(
        ctx,
        name=vnet_rule,
        server_name=postgresql_server,
        resource_group=resource_group,
        subnet_id=subnet_id,
        ignore_missing_endpoint=ignore_missing_endpoint,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("virtual_network_subnet_id")
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, vnet_rule, postgresql_server, resource_group, subnet, vnet,
):
    ignore_missing_endpoint = False
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"
    missing_endpoint_flag = True
    expected = {
        "changes": {
            "ignore_missing_vnet_service_endpoint": {
                "new": missing_endpoint_flag,
                "old": ignore_missing_endpoint,
            },
        },
        "comment": f"Virtual Network Rule {vnet_rule} has been updated.",
        "name": vnet_rule,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.virtual_network_rule.present(
        ctx,
        name=vnet_rule,
        server_name=postgresql_server,
        resource_group=resource_group,
        subnet_id=subnet_id,
        ignore_missing_endpoint=missing_endpoint_flag,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, vnet_rule, postgresql_server, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": vnet_rule,},},
        "comment": f"Virtual Network Rule {vnet_rule} has been deleted.",
        "name": vnet_rule,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.virtual_network_rule.absent(
        ctx, vnet_rule, postgresql_server, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
