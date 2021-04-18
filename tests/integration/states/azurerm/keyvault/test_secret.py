import pytest


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, keyvault):
    expected = {
        "changes": {
            "new": {
                "name": "secretname",
                "properties": {
                    "content_type": None,
                    "enabled": True,
                    "expires_on": None,
                    "key_id": None,
                    "name": "secretname",
                    "not_before": None,
                    "recovery_level": "Purgeable",
                    "tags": None,
                    "vault_url": f"https://{keyvault}.vault.azure.net",
                },
                "value": "REDACTED",
            },
            "old": {},
        },
        "comment": "Secret secretname has been created.",
        "name": "secretname",
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.secret.present(
        ctx, "secretname", "supersecret", f"https://{keyvault}.vault.azure.net/",
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"]["properties"].pop("created_on")
    ret["changes"]["new"]["properties"].pop("updated_on")
    ret["changes"]["new"]["properties"].pop("id")
    ret["changes"]["new"]["properties"].pop("version")
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, keyvault, tags):
    expected = {
        "changes": {
            "tags": {"new": tags,},
            "content_type": {"new": "text/plain", "old": None},
        },
        "comment": f"Secret secretname has been updated.",
        "name": "secretname",
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.secret.present(
        ctx,
        "secretname",
        "supersecret",
        f"https://{keyvault}.vault.azure.net/",
        content_type="text/plain",
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, keyvault, tags):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": "secretname",
                "properties": {
                    "name": "secretname",
                    "content_type": "text/plain",
                    "enabled": True,
                    "expires_on": None,
                    "not_before": None,
                    "key_id": None,
                    "recovery_level": "Purgeable",
                    "vault_url": f"https://{keyvault}.vault.azure.net",
                    "tags": tags,
                },
                "value": "supersecret",
            },
        },
        "comment": f"Secret secretname has been deleted.",
        "name": "secretname",
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.secret.absent(
        ctx, "secretname", f"https://{keyvault}.vault.azure.net/",
    )
    expected["changes"]["old"]["id"] = ret["changes"]["old"]["id"]
    expected["changes"]["old"]["properties"]["id"] = ret["changes"]["old"][
        "properties"
    ]["id"]
    expected["changes"]["old"]["properties"]["version"] = ret["changes"]["old"][
        "properties"
    ]["version"]
    expected["changes"]["old"]["properties"]["created_on"] = ret["changes"]["old"][
        "properties"
    ]["created_on"]
    expected["changes"]["old"]["properties"]["updated_on"] = ret["changes"]["old"][
        "properties"
    ]["updated_on"]
    assert ret == expected
