import pytest


@pytest.fixture(scope="session")
def key_type():
    yield "RSA"


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, test_key, key_type, test_keyvault):
    vault_url = f"https://{test_keyvault}.vault.azure.net/"
    expected = {
        "changes": {
            "new": {"name": test_key, "key_type": key_type, "enabled": False,},
            "old": {},
        },
        "comment": f"Key {test_key} has been created.",
        "name": test_key,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.key.present(
        ctx, name=test_key, key_type=key_type, vault_url=vault_url, enabled=False,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, test_key, key_type, test_keyvault):
    vault_url = f"https://{test_keyvault}.vault.azure.net/"
    expected = {
        "changes": {"enabled": {"new": True, "old": False}},
        "comment": f"Key {test_key} has been updated.",
        "name": test_key,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.key.present(
        ctx, name=test_key, key_type=key_type, vault_url=vault_url, enabled=True,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, test_key, test_keyvault):
    vault_url = f"https://{test_keyvault}.vault.azure.net/"
    expected = {
        "changes": {"new": {}, "old": {"name": test_key}},
        "comment": f"Key {test_key} has been deleted.",
        "name": test_key,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.key.absent(
        ctx, name=test_key, vault_url=vault_url
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
