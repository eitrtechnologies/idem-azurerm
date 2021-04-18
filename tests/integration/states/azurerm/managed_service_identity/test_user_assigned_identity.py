import pytest
import random
import string


@pytest.fixture(scope="session")
def identity():
    yield "identity-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_present(hub, ctx, identity, resource_group, location):
    expected = {
        "changes": {
            "new": {
                "name": identity,
                "location": location,
                "tags": {},
                "type": "Microsoft.ManagedIdentity/userAssignedIdentities",
            },
            "old": {},
        },
        "comment": f"User assigned identity {identity} has been created.",
        "name": identity,
        "result": True,
    }
    ret = await hub.states.azurerm.managed_service_identity.user_assigned_identity.present(
        ctx, name=identity, resource_group=resource_group,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("tenant_id")
    ret["changes"]["new"].pop("client_id")
    ret["changes"]["new"].pop("principal_id")
    assert ret == expected


@pytest.mark.run(order=2, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, identity, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags},},
        "comment": f"User assigned identity {identity} has been updated.",
        "name": identity,
        "result": True,
    }
    ret = await hub.states.azurerm.managed_service_identity.user_assigned_identity.present(
        ctx, name=identity, resource_group=resource_group, tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_absent(hub, ctx, identity, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": identity,},},
        "comment": f"User assigned identity {identity} has been deleted.",
        "name": identity,
        "result": True,
    }
    ret = await hub.states.azurerm.managed_service_identity.user_assigned_identity.absent(
        ctx, name=identity, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
