import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, zone, resource_group):
    expected = {
        "changes": {
            "new": {
                "name": zone,
                "resource_group": resource_group,
                "etag": None,
                "registration_virtual_networks": None,
                "resolution_virtual_networks": None,
                "tags": None,
                "zone_type": "Public",
            },
            "old": {},
        },
        "comment": f"DNS zone {zone} has been created.",
        "name": zone,
        "result": True,
    }
    ret = await hub.states.azurerm.dns.zone.present(
        ctx, name=zone, resource_group=resource_group,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, zone, resource_group, tags):
    expected = {
        "changes": {"tags": {"new": tags},},
        "comment": f"DNS zone {zone} has been updated.",
        "name": zone,
        "result": True,
    }
    ret = await hub.states.azurerm.dns.zone.present(
        ctx, name=zone, resource_group=resource_group, tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, zone, resource_group):
    expected = {
        "changes": {"new": {}, "old": {"name": zone,},},
        "comment": f"DNS zone {zone} has been deleted.",
        "name": zone,
        "result": True,
    }
    ret = await hub.states.azurerm.dns.zone.absent(ctx, zone, resource_group)
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
