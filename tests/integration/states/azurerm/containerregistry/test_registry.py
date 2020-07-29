import pytest


@pytest.mark.second
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, acr):
    resource_group = "rg-idem"
    expected = {
        "changes": {
            "new": {
                "admin_user_enabled": False,
                "name": acr,
                "resource_group": resource_group,
                "sku": "Basic",
                "replica_locations": [],
            },
            "old": {},
        },
        "comment": f"Container registry {acr} has been created.",
        "name": acr,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.registry.present(
        ctx, acr, resource_group, sku="Basic", location=location,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, acr, tags):
    resource_group = "rg-idem"
    expected = {
        "changes": {"tags": {"new": tags,},},
        "comment": f"Container registry {acr} has been updated.",
        "name": acr,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.registry.present(
        ctx, acr, resource_group, sku="Basic", location=location, tags=tags,
    )
    assert ret == expected


@pytest.mark.second_to_last
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, acr, tags):
    resource_group = "rg-idem"
    expected = {
        "changes": {
            "new": {},
            "old": {
                "admin_user_enabled": False,
                "location": location,
                "name": acr,
                "policies": {
                    "quarantine_policy": {"status": "disabled"},
                    "retention_policy": {"days": 7, "status": "disabled"},
                    "trust_policy": {"type": "Notary", "status": "disabled"},
                },
                "sku": {"name": "Basic", "tier": "Basic"},
                "provisioning_state": "Succeeded",
                "type": "Microsoft.ContainerRegistry/registries",
                "tags": tags,
            },
        },
        "comment": f"Container registry {acr} has been deleted.",
        "name": acr,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.registry.absent(
        ctx, acr, resource_group
    )
    ret["changes"]["old"].pop("id")
    ret["changes"]["old"].pop("login_server")
    ret["changes"]["old"].pop("creation_date")
    ret["changes"]["old"]["policies"]["retention_policy"].pop("last_updated_time")
    assert ret == expected
