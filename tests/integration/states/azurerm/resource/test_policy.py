import pytest
import random
import string


@pytest.fixture(scope="session")
def def_name():
    yield "idem-policy" + "".join(
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


@pytest.fixture(scope="module")
def assignment_name():
    yield "AllowedLocations"


@pytest.fixture(scope="module")
def assignment_description():
    yield "This policy enables restriction of locations you can specify when deploying resources"


@pytest.fixture(scope="module")
def assignment_params():
    yield {
        "listOfAllowedLocations": {
            "value": [
                "centralus",
                "eastus",
                "eastus2",
                "northcentralus",
                "southcentralus",
                "westcentralus",
                "westus",
                "westus2",
            ]
        }
    }


"""
        Restrict Allowed Locations :
            azurerm.resource.policy.assignment_present :
                - name: AllowedLocations
                - scope: /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852
                - definition_name: e56962a6-4747-49cd-b67b-bf8b01975c4c
                - display_name: Allowed Locations
                - description: This policy enables restriction of locations you can specify when deploying resources
                - parameters:
                      listOfAllowedLocations:
                          value:
                              - centralus
                              - eastus
                              - eastus2
                              - northcentralus
                              - southcentralus
                              - westcentralus
                              - westus
                              - westus2
"""


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


@pytest.mark.run(after="test_definition_present", before="test_definition_absent")
@pytest.mark.asyncio
async def test_definition_changes(hub, ctx, def_name, def_policy_rule):
    metadata = {"policy_creator": "EITR Technologies"}
    expected = {
        "changes": {"metadata": {"new": metadata, "old": None},},
        "comment": f"Policy definition {def_name} has been updated.",
        "name": def_name,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.policy.definition_present(
        ctx, name=def_name, policy_rule=def_policy_rule, metadata=metadata
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
    ret = await hub.states.azurerm.resource.policy.definition_absent(ctx, def_name)
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
