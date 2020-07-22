import pytest
import random
import string


@pytest.fixture(scope="session")
def def_name():
    yield "idem-policy-definition-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="module")
def def_policy_rule():
    yield {
        "then": {"effect": "deny"},
        "if": {
            "allOf": [
                {
                    "source": "action",
                    "equals": "Microsoft.Compute/virtualMachines/write",
                },
                {"field": "location", "in": ["eastus", "eastus2", "centralus"]},
            ]
        },
    }


@pytest.fixture(scope="session")
def assignment_name():
    yield "idem-policy-assignment-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=1)
@pytest.mark.asyncio
async def test_definition_present(hub, ctx, def_name, def_policy_rule):
    expected = {
        "changes": {
            "new": {
                "description": None,
                "display_name": None,
                "metadata": None,
                "mode": None,
                "name": def_name,
                "parameters": None,
                "policy_rule": def_policy_rule,
                "policy_type": None,
            },
            "old": {},
        },
        "comment": f"Policy definition {def_name} has been created.",
        "name": def_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.definition_present(
        ctx, name=def_name, policy_rule=def_policy_rule,
    )
    assert ret == expected


@pytest.mark.run(
    order=1, after="test_definition_present", before="test_definition_changes"
)
@pytest.mark.asyncio
async def test_definition_changes(hub, ctx, def_name, def_policy_rule):
    desc = "test"
    expected = {
        "changes": {"description": {"new": desc, "old": None},},
        "comment": f"Policy definition {def_name} has been updated.",
        "name": def_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.definition_present(
        ctx, name=def_name, policy_rule=def_policy_rule, description=desc
    )
    assert ret == expected


@pytest.mark.run(
    order=1, after="test_definition_changes", before="test_assignment_changes"
)
@pytest.mark.asyncio
async def test_assignment_present(hub, ctx, assignment_name, def_name):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    scope = f"/subscriptions/{subscription_id}"
    expected = {
        "changes": {
            "new": {
                "name": assignment_name,
                "scope": scope,
                "definition_name": def_name,
                "parameters": None,
                "display_name": None,
                "description": None,
            },
            "old": {},
        },
        "comment": f"Policy assignment {assignment_name} has been created.",
        "name": assignment_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.assignment_present(
        ctx, name=assignment_name, scope=scope, definition_name=def_name,
    )
    assert ret == expected


@pytest.mark.run(
    order=1, after="test_assigment_present", before="test_assignment_absent"
)
@pytest.mark.asyncio
async def test_assignment_changes(hub, ctx, assignment_name, def_name):
    desc = "test"
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    scope = f"/subscriptions/{subscription_id}"
    changed_display_name = "Locations Allowed for Subscription"
    expected = {
        "changes": {"description": {"new": desc, "old": None}},
        "comment": f"Policy assignment {assignment_name} has been updated.",
        "name": assignment_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.assignment_present(
        ctx,
        name=assignment_name,
        scope=scope,
        definition_name=def_name,
        description=desc,
    )
    assert ret == expected


@pytest.mark.run(
    order=-1, after="test_assignment_changes", before="test_definition_absent"
)
@pytest.mark.asyncio
async def test_assignment_absent(hub, ctx, assignment_name):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    scope = f"/subscriptions/{subscription_id}"
    expected = {
        "changes": {"new": {}, "old": {"name": assignment_name,},},
        "comment": f"Policy assignment {assignment_name} has been deleted.",
        "name": assignment_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.assignment_absent(
        ctx, name=assignment_name, scope=scope
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=-1)
@pytest.mark.asyncio
async def test_definition_absent(hub, ctx, def_name):
    expected = {
        "changes": {"new": {}, "old": {"name": def_name,},},
        "comment": f"Policy defintion {def_name} has been deleted.",
        "name": def_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.definition_absent(ctx, name=def_name)
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
