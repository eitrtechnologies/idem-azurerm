import pytest
import random
import string


@pytest.fixture(scope="session")
def nsg():
    yield "nsg-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def rule():
    yield "nsg-rule-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, nsg, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": nsg,
                "security_rules": [],
                "location": "eastus",
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/networkSecurityGroups",
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
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("etag")
    ret["changes"]["new"].pop("default_security_rules")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, nsg, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags}},
        "comment": f"Network security group {nsg} has been updated.",
        "name": nsg,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.present(
        ctx, name=nsg, resource_group=resource_group, tags=tags
    )
    assert ret == expected


@pytest.mark.run(order=3, after="test_changes", before="test_rule_changes")
@pytest.mark.asyncio
async def test_rule_present(
    hub, ctx, nsg, resource_group, rule,
):
    expected = {
        "changes": {
            "new": {
                "name": rule,
                "priority": 100,
                "protocol": "tcp",
                "access": "Allow",
                "direction": "Outbound",
                "source_address_prefix": "virtualnetwork",
                "source_address_prefixes": [],
                "destination_address_prefix": "internet",
                "destination_port_range": "*",
                "destination_port_ranges": [],
                "destination_address_prefixes": [],
                "source_port_range": "*",
                "source_port_ranges": [],
                "provisioning_state": "Succeeded",
            },
            "old": {},
        },
        "comment": f"Security rule {rule} has been created.",
        "name": rule,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.security_rule_present(
        ctx,
        name=rule,
        security_group=nsg,
        resource_group=resource_group,
        priority=100,
        access="allow",
        protocol="tcp",
        direction="outbound",
        source_address_prefix="virtualnetwork",
        destination_address_prefix="internet",
        source_port_range="*",
        destination_port_range="*",
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    assert ret == expected


@pytest.mark.run(order=3, after="test_rule_present", before="test_rule_absent")
@pytest.mark.asyncio
async def test_rule_changes(hub, ctx, nsg, resource_group, rule):
    expected = {
        "changes": {"priority": {"new": 101, "old": 100}},
        "comment": f"Security rule {rule} has been updated.",
        "name": rule,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.security_rule_present(
        ctx,
        name=rule,
        security_group=nsg,
        resource_group=resource_group,
        priority=101,
        access="allow",
        protocol="tcp",
        direction="outbound",
        source_address_prefix="virtualnetwork",
        destination_address_prefix="internet",
        source_port_range="*",
        destination_port_range="*",
    )
    assert ret == expected


@pytest.mark.run(order=-3, after="test_rule_changes", before="test_absent")
@pytest.mark.asyncio
async def test_rule_absent(hub, ctx, nsg, resource_group, rule):
    expected = {
        "changes": {"new": {}, "old": {"name": rule,},},
        "comment": f"Security rule {rule} has been deleted.",
        "name": rule,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.security_rule_absent(
        ctx, name=rule, security_group=nsg, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=-3, after="test_rule_absent")
@pytest.mark.asyncio
async def test_absent(hub, ctx, nsg, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": nsg,},},
        "comment": f"Network security group {nsg} has been deleted.",
        "name": nsg,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_security_group.absent(
        ctx, name=nsg, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
