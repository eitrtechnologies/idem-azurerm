import pytest
import string
import random


@pytest.fixture(scope="module")
def record_type():
    yield "A"


@pytest.fixture(scope="session")
def record_set():
    yield "idem-record-set-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, record_set, zone, resource_group, record_type):
    expected = {
        "changes": {
            "new": {
                "name": record_set,
                "resource_group": resource_group,
                "zone_name": zone,
                "record_type": record_type,
                "etag": None,
                "metadata": None,
                "ttl": None,
            },
            "old": {},
        },
        "comment": f"Record set {record_set} has been created.",
        "name": record_set,
        "result": True,
    }
    ret = await hub.states.azurerm.dns.record_set.present(
        ctx,
        name=record_set,
        resource_group=resource_group,
        zone_name=zone,
        record_type=record_type,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, record_set, zone, resource_group, record_type):
    metadata = {"zone": zone}
    expected = {
        "changes": {"metadata": {"new": metadata},},
        "comment": f"Record set {record_set} has been updated.",
        "name": record_set,
        "result": True,
    }
    ret = await hub.states.azurerm.dns.record_set.present(
        ctx,
        name=record_set,
        resource_group=resource_group,
        zone_name=zone,
        record_type=record_type,
        metadata=metadata,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, record_set, zone, resource_group, record_type):
    expected = {
        "changes": {"new": {}, "old": {"name": record_set,},},
        "comment": f"Record set {record_set} has been deleted.",
        "name": record_set,
        "result": True,
    }

    ret2 = await hub.exec.azurerm.dns.record_set.get(
        ctx, record_set, zone, resource_group, record_type
    )

    ret = await hub.states.azurerm.dns.record_set.absent(
        ctx,
        name=record_set,
        zone_name=zone,
        resource_group=resource_group,
        record_type=record_type,
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
