import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, acr):
    hook = "idemhook"
    expected = {
        "changes": {
            "new": {
                "actions": ["push"],
                "name": hook,
                "registry_name": acr,
                "resource_group": resource_group,
                "service_uri": "http://idem.eitr.tech/webhook",
                "status": "enabled",
            },
            "old": {},
        },
        "comment": f"Container registry webhook {hook} has been created.",
        "name": hook,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.webhook.present(
        ctx, hook, acr, resource_group, "http://idem.eitr.tech/webhook", ["push"]
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, acr, tags):
    hook = "idemhook"
    expected = {
        "changes": {"tags": {"new": tags,},},
        "comment": f"Container registry webhook {hook} has been updated.",
        "name": hook,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.webhook.present(
        ctx,
        hook,
        acr,
        resource_group,
        "http://idem.eitr.tech/webhook",
        ["push"],
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, acr, tags):
    hook = "idemhook"
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": hook,
                "actions": ["push"],
                "location": location,
                "provisioning_state": "Succeeded",
                "scope": "",
                "status": "enabled",
                "tags": tags,
                "type": "Microsoft.ContainerRegistry/registries/webhooks",
            },
        },
        "comment": f"Container registry webhook {hook} has been deleted.",
        "name": hook,
        "result": True,
    }
    ret = await hub.states.azurerm.containerregistry.webhook.absent(
        ctx, hook, acr, resource_group
    )
    ret["changes"]["old"].pop("id")
    assert ret == expected
