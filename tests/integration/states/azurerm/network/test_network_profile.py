import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group):
    prf = "idemprofile"
    expected = {
        "changes": {
            "new": {
                "name": prf,
                "container_network_interface_configurations": [],
                "container_network_interfaces": [],
                "location": "eastus",
                "provisioning_state": "Succeeded",
                "type": "Microsoft.Network/networkProfiles",
            },
            "old": {},
        },
        "comment": f"Network profile {prf} has been created.",
        "name": prf,
        "result": True,
    }
    ret = await hub.states.azurerm.network.network_profile.present(
        ctx, prf, resource_group
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("resource_guid")
    ret["changes"]["new"].pop("etag")
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, tags):
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
