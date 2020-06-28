import pytest


# TODO: move this into a fixture
KEYVAULT = "kv-idem-inttest"


@pytest.mark.run(before="test_absent")
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location):
    tenant_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("tenant")
    object_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("client_id")
    sku = "standard"
    access_policies = [
        {
            "tenant_id": tenant_id,
            "object_id": object_id,
            "permissions": {
                "keys": [
                    "Get",
                    "List",
                    "Update",
                    "Create",
                    "Import",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                    "UnwrapKey",
                    "WrapKey",
                    "Verify",
                    "Sign",
                    "Encrypt",
                    "Decrypt",
                ],
                "secrets": [
                    "Get",
                    "List",
                    "Set",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                ],
            },
        }
    ]
    expected = {
        "changes": {
            "new": {
                "access_policies": access_policies,
                "enable_soft_delete": True,
                "location": location,
                "name": KEYVAULT,
                "tenant_id": tenant_id,
                "resource_group": resource_group,
                "sku": "standard",
            },
            "old": {},
        },
        "comment": f"Key Vault {KEYVAULT} has been created.",
        "name": KEYVAULT,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.vault.present(
        ctx,
        KEYVAULT,
        resource_group,
        location,
        tenant_id,
        sku,
        access_policies=access_policies,
        enable_soft_delete=True,
    )
    assert ret == expected


@pytest.mark.run(after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, tags):
    tenant_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("tenant")
    object_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("client_id")
    sku = "standard"
    access_policies = [
        {
            "tenant_id": tenant_id,
            "object_id": object_id,
            "permissions": {
                "keys": [
                    "Get",
                    "List",
                    "Update",
                    "Create",
                    "Import",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                    "UnwrapKey",
                    "WrapKey",
                    "Verify",
                    "Sign",
                    "Encrypt",
                    "Decrypt",
                ],
                "secrets": [
                    "Get",
                    "List",
                    "Set",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                ],
            },
        }
    ]
    expected = {
        "changes": {
            "tags": {"new": tags,},
            "access_policies": {"old": access_policies, "new": None},
        },
        "comment": f"Key Vault {KEYVAULT} has been updated.",
        "name": KEYVAULT,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.vault.present(
        ctx, KEYVAULT, resource_group, location, tenant_id, sku, tags=tags
    )
    assert ret == expected


@pytest.mark.run(after="test_present")
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, tags):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    tenant_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("tenant")
    object_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("client_id")
    access_policies = [
        {
            "tenant_id": tenant_id,
            "object_id": object_id,
            "permissions": {
                "keys": [
                    "Get",
                    "List",
                    "Update",
                    "Create",
                    "Import",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                    "UnwrapKey",
                    "WrapKey",
                    "Verify",
                    "Sign",
                    "Encrypt",
                    "Decrypt",
                ],
                "secrets": [
                    "Get",
                    "List",
                    "Set",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                ],
            },
        }
    ]
    expected = {
        "changes": {
            "new": {},
            "old": {
                "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.KeyVault/vaults/{KEYVAULT}",
                "location": location,
                "name": KEYVAULT,
                "properties": {
                    "access_policies": [],
                    "enable_soft_delete": True,
                    "enabled_for_deployment": False,
                    "sku": {"family": "A", "name": "standard"},
                    "tenant_id": f"{tenant_id}",
                    "vault_uri": f"https://{KEYVAULT}.vault.azure.net/",
                },
                "tags": tags,
                "type": "Microsoft.KeyVault/vaults",
            },
        },
        "comment": f"Key Vault {KEYVAULT} has been deleted.",
        "name": KEYVAULT,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.vault.absent(ctx, KEYVAULT, resource_group)
    assert ret == expected
