import pytest
import random
import string


@pytest.fixture(scope="session")
def nsg():
    yield "nsg-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, nsg, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": nsg,
                "tags": None,
                "resource_group": resource_group,
                "security_rules": None,
            },
            "old": {},
        },
        "comment": f"Network security group {nsg} has been created.",
        "name": nsg,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.present(
        ctx, name=nsg, resource_group=resource_group
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, nsg, resource_group, tags):
    rules = [
        {
            "name": "allow_all_outbound",
            "priority": 100,
            "protocol": "tcp",
            "access": "allow",
            "direction": "outbound",
            "source_address_prefix": "virtualnetwork",
            "destination_address_prefix": "internet",
            "source_port_range": "*",
            "destination_port_range": "*",
        }
    ]
    expected = {
        "changes": {"tags": {"new": tags}, "security_rules": {"new": rules, "old": []}},
        "comment": f"Network security group {nsg} has been updated.",
        "name": nsg,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.present(
        ctx, name=nsg, resource_group=resource_group, security_rules=rules, tags=tags
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, nsg, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": nsg,},},
        "comment": f"Network security group {nsg} has been deleted.",
        "name": nsg,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.absent(
        ctx, nsg, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
