import pytest
import random
import string


@pytest.fixture(scope="session")
def bastion_host():
    yield "bastion-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
@pytest.mark.asyncio
@pytest.mark.slow
async def test_present(hub, ctx, bastion_host, resource_group, vnet, public_ip_addr):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    pub_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{public_ip_addr}"
    subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/AzureBastionSubnet"
    ip_config = {
        "name": "bastion-idem-config",
        "subnet": subnet_id,
        "public_ip_address": pub_ip_id,
    }
    expected = {
        "changes": {
            "new": {
                "name": bastion_host,
                "location": "eastus",
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/bastionHosts",
                "ip_configurations": [
                    {
                        "name": "bastion-idem-config",
                        "private_ip_allocation_method": "Dynamic",
                        "provisioning_state": "Succeeded",
                        "type": "Microsoft.Network/bastionHosts/bastionHostIpConfigurations",
                        "public_ip_address": {"id": pub_ip_id},
                        "subnet": {"id": subnet_id},
                    }
                ],
            },
            "old": {},
        },
        "comment": f"Bastion Host {bastion_host} has been created.",
        "name": bastion_host,
        "result": True,
    }
    ret = await hub.states.azurerm.network.bastion_host.present(
        ctx,
        name=bastion_host,
        resource_group=resource_group,
        ip_configuration=ip_config,
    )
    ret["changes"]["new"].pop("etag")
    ret["changes"]["new"].pop("id")
    expected["changes"]["new"]["dns_name"] = ret["changes"]["new"].get("dns_name")
    ret["changes"]["new"]["ip_configurations"][0].pop("id")
    ret["changes"]["new"]["ip_configurations"][0].pop("etag")
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
@pytest.mark.slow
async def test_changes(
    hub, ctx, bastion_host, resource_group, vnet, public_ip_addr, tags
):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    pub_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{public_ip_addr}"
    subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/AzureBastionSubnet"
    ip_config = {
        "name": "bastion-idem-config",
        "subnet": subnet_id,
        "public_ip_address": pub_ip_id,
    }
    expected = {
        "changes": {
            "tags": {"new": tags},
        },
        "comment": f"Bastion Host {bastion_host} has been updated.",
        "name": bastion_host,
        "result": True,
    }
    ret = await hub.states.azurerm.network.bastion_host.present(
        ctx,
        name=bastion_host,
        resource_group=resource_group,
        ip_configuration=ip_config,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
@pytest.mark.slow
async def test_absent(hub, ctx, bastion_host, resource_group):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": bastion_host,
            },
        },
        "comment": f"Bastion Host {bastion_host} has been deleted.",
        "name": bastion_host,
        "result": True,
    }
    ret = await hub.states.azurerm.network.bastion_host.absent(
        ctx, bastion_host, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
