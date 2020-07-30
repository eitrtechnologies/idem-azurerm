import pytest
import random
import string


@pytest.fixture(scope="session")
def key():
    yield "key-idem-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_present(hub, ctx, key, keyvault):
    key_type = "RSA"
    vault_url = f"https://{keyvault}.vault.azure.net/"
    expected = {
        "changes": {
            "new": {"name": key, "key_type": key_type, "enabled": False,},
            "old": {},
        },
        "comment": f"Key {key} has been created.",
        "name": key,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.key.present(
        ctx, name=key, key_type=key_type, vault_url=vault_url, enabled=False,
    )
    assert ret == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, key, keyvault):
    key_type = "RSA"
    vault_url = f"https://{keyvault}.vault.azure.net/"
    expected = {
        "changes": {"enabled": {"new": True, "old": False}},
        "comment": f"Key {key} has been updated.",
        "name": key,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.key.present(
        ctx, name=key, key_type=key_type, vault_url=vault_url, enabled=True,
    )
    assert ret == expected


@pytest.mark.run(order=-4)
@pytest.mark.asyncio
async def test_absent(hub, ctx, key, keyvault):
    vault_url = f"https://{keyvault}.vault.azure.net/"
    expected = {
        "changes": {"new": {}, "old": {"name": key}},
        "comment": f"Key {key} has been deleted.",
        "name": key,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.key.absent(
        ctx, name=key, vault_url=vault_url
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
