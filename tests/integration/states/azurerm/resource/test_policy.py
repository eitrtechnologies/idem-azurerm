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


@pytest.mark.skip(
    reason="Need to inquire about the way changes are done in this module"
)
@pytest.mark.run(
    order=1, after="test_definition_present", before="test_definition_absent"
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
