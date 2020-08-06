import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group):
    resource_group = "rg-idem"
    prf = "idemprofile"
    expected = {
        "changes": {
            "new": {"name": prf, "resource_group": resource_group,},
            "old": {},
        },
        "comment": f"Network profile {prf} has been created.",
        "name": prf,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_profile.present(
        ctx, prf, resource_group
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, acr, tags):
    resource_group = "rg-idem"
    prf = "idemprofile"
    expected = {
        "changes": {"tags": {"new": tags,},},
        "comment": f"Network profile {prf} has been updated.",
        "name": prf,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_profile.present(
        ctx, prf, resource_group, tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, tags):
    resource_group = "rg-idem"
    prf = "idemprofile"
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": prf,
                "location": location,
                "container_network_interfaces": [],
                "container_network_interface_configurations": [],
                "provisioning_state": "Succeeded",
                "tags": tags,
                "type": "Microsoft.Network/networkProfiles",
            },
        },
        "comment": f"Network profile {prf} has been deleted.",
        "name": prf,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_profile.absent(
        ctx, prf, resource_group
    )
    ret["changes"]["old"].pop("id")
    ret["changes"]["old"].pop("etag")
    ret["changes"]["old"].pop("resource_guid")
    assert ret == expected
