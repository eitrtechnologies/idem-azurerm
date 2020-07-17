import pytest


@pytest.fixture(scope="module")
def fw_rule():
    yield "idem-fw-rule1"


@pytest.fixture(scope="module")
def start_addr():
    yield "10.0.0.0"


@pytest.fixture(scope="module")
def end_addr():
    yield "10.0.0.255"


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(
    hub, ctx, fw_rule, postgresql_server, resource_group, start_addr, end_addr
):
    expected = {
        "changes": {
            "new": {
                "name": fw_rule,
                "server_name": postgresql_server,
                "resource_group": resource_group,
                "start_ip_address": start_addr,
                "end_ip_address": end_addr,
            },
            "old": {},
        },
        "comment": f"Firewall Rule {fw_rule} has been created.",
        "name": fw_rule,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.firewall_rule.present(
        ctx,
        name=fw_rule,
        server_name=postgresql_server,
        resource_group=resource_group,
        start_ip_address=start_addr,
        end_ip_address=end_addr,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(
    hub, ctx, fw_rule, postgresql_server, resource_group, start_addr, end_addr
):
    changed_end_addr = "10.0.0.254"
    expected = {
        "changes": {"end_ip_address": {"new": changed_end_addr, "old": end_addr},},
        "comment": f"Firewall Rule {fw_rule} has been updated.",
        "name": fw_rule,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.firewall_rule.present(
        ctx,
        name=fw_rule,
        server_name=postgresql_server,
        resource_group=resource_group,
        start_ip_address=start_addr,
        end_ip_address=changed_end_addr,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, fw_rule, postgresql_server, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": fw_rule,},},
        "comment": f"Firewall Rule {fw_rule} has been deleted.",
        "name": fw_rule,
        "result": True,
    }
    ret = await hub.states.azurerm.postgresql.firewall_rule.absent(
        ctx, fw_rule, postgresql_server, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
