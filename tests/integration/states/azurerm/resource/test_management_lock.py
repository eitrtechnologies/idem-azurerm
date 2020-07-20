import pytest
import random
import string


@pytest.fixture(scope="session")
def lock():
    yield "idem-lock-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def scope_lock():
    yield "idem-lock-scope-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def resource_lock():
    yield "idem-lock-resource-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="module")
def level():
    yield "ReadOnly"


@pytest.fixture(scope="module")
def updated_notes():
    yield "This is a test lock"


@pytest.fixture(scope="module")
def resource_type():
    yield "virtualNetworks"


@pytest.fixture(scope="module")
def resource_provider_namespace():
    yield "Microsoft.Network"


@pytest.mark.run(order=5)
@pytest.mark.asyncio
async def test_present(hub, ctx, lock, level, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": lock,
                "resource_group": resource_group,
                "lock_level": level,
            },
            "old": {},
        },
        "comment": f"Management lock {lock} has been created.",
        "name": lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.present(
        ctx, name=lock, lock_level=level, resource_group=resource_group
    )
    assert ret == expected


@pytest.mark.run(order=5, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, lock, level, resource_group, updated_notes):
    expected = {
        "changes": {"notes": {"new": updated_notes, "old": None},},
        "comment": f"Management lock {lock} has been updated.",
        "name": lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.present(
        ctx,
        name=lock,
        lock_level=level,
        resource_group=resource_group,
        notes=updated_notes,
    )
    assert ret == expected


@pytest.mark.run(order=-5, before="test_absent_by_scope")
@pytest.mark.asyncio
async def test_absent(hub, ctx, lock, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": lock,},},
        "comment": f"Management lock {lock} has been deleted.",
        "name": lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.absent(
        ctx, name=lock, resource_group=resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=5, after="test_absent")
@pytest.mark.asyncio
async def test_present_by_scope(hub, ctx, scope_lock, level, resource_group):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    scope = f"/subscriptions/{subscription_id}/resourcegroups/{resource_group}"
    expected = {
        "changes": {
            "new": {"name": scope_lock, "scope": scope, "lock_level": level,},
            "old": {},
        },
        "comment": f"Management lock {scope_lock} has been created.",
        "name": scope_lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.present_by_scope(
        ctx, name=scope_lock, lock_level=level, scope=scope
    )
    assert ret == expected


@pytest.mark.run(order=5, after="test_present_by_scope", before="test_absent_by_scope")
@pytest.mark.asyncio
async def test_changes_by_scope(
    hub, ctx, scope_lock, level, resource_group, updated_notes
):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    scope = f"/subscriptions/{subscription_id}/resourcegroups/{resource_group}"
    expected = {
        "changes": {"notes": {"new": updated_notes, "old": None},},
        "comment": f"Management lock {scope_lock} has been updated.",
        "name": scope_lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.present_by_scope(
        ctx, name=scope_lock, lock_level=level, scope=scope, notes=updated_notes,
    )
    assert ret == expected


@pytest.mark.run(order=-5, after="test_absent")
@pytest.mark.asyncio
async def test_absent_by_scope(hub, ctx, scope_lock, resource_group):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    scope = f"/subscriptions/{subscription_id}/resourcegroups/{resource_group}"
    expected = {
        "changes": {"new": {}, "old": {"name": scope_lock,},},
        "comment": f"Management lock {scope_lock} has been deleted.",
        "name": scope_lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.absent_by_scope(
        ctx, name=scope_lock, scope=scope
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]


@pytest.mark.run(order=5, after="test_absent_by_scope")
@pytest.mark.asyncio
async def test_present_at_resource_level(
    hub,
    ctx,
    resource_lock,
    level,
    resource_provider_namespace,
    resource_type,
    resource_group,
    vnet,
):
    expected = {
        "changes": {
            "new": {
                "name": resource_lock,
                "resource_group": resource_group,
                "lock_level": level,
                "resource_type": resource_type,
                "resource": vnet,
                "resource_provider_namespace": resource_provider_namespace,
            },
            "old": {},
        },
        "comment": f"Management lock {resource_lock} has been created.",
        "name": resource_lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.present_at_resource_level(
        ctx,
        name=resource_lock,
        lock_level=level,
        resource_group=resource_group,
        resource_provider_namespace=resource_provider_namespace,
        resource_type=resource_type,
        resource=vnet,
    )
    assert ret == expected


@pytest.mark.run(
    order=5,
    after="test_present_at_resource_level",
    before="test_absent_at_resource_level",
)
@pytest.mark.asyncio
async def test_changes_at_resource_level(
    hub,
    ctx,
    resource_lock,
    level,
    resource_provider_namespace,
    resource_type,
    resource_group,
    vnet,
    updated_notes,
):
    expected = {
        "changes": {"notes": {"new": updated_notes, "old": None},},
        "comment": f"Management lock {resource_lock} has been updated.",
        "name": resource_lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.present_at_resource_level(
        ctx,
        name=resource_lock,
        lock_level=level,
        resource_group=resource_group,
        resource_provider_namespace=resource_provider_namespace,
        resource_type=resource_type,
        resource=vnet,
        notes=updated_notes,
    )
    assert ret == expected


@pytest.mark.run(order=-5, after="test_absent_by_scope")
@pytest.mark.asyncio
async def test_absent_at_resource_level(
    hub,
    ctx,
    resource_lock,
    level,
    resource_group,
    resource_provider_namespace,
    resource_type,
    vnet,
):
    expected = {
        "changes": {"new": {}, "old": {"name": resource_lock,},},
        "comment": f"Management lock {resource_lock} has been deleted.",
        "name": resource_lock,
        "result": True,
    }
    ret = await hub.states.azurerm.resource.management_lock.absent_at_resource_level(
        ctx,
        name=resource_lock,
        lock_level=level,
        resource_group=resource_group,
        resource_provider_namespace=resource_provider_namespace,
        resource_type=resource_type,
        resource=vnet,
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
