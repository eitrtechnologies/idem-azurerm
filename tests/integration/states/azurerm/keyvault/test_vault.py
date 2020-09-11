import pytest
import time


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, keyvault):
    tenant_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("tenant")
    app_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("client_id")
    object_id = next(
        iter(
            await hub.exec.azurerm.graphrbac.service_principal.list(
                ctx, sp_filter=f"appId eq '{app_id}'"
            )
        )
    )

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
                "name": keyvault,
                "location": location,
                "properties": {
                    "access_policies": access_policies,
                    "enable_rbac_authorization": False,
                    "enable_soft_delete": False,
                    "enabled_for_deployment": False,
                    "tenant_id": tenant_id,
                    "sku": {"name": sku, "family": "A"},
                    "soft_delete_retention_in_days": 90,
                    "vault_uri": f"https://{keyvault}.vault.azure.net/",
                },
                "type": "Microsoft.KeyVault/vaults",
                "tags": {},
            },
            "old": {},
        },
        "comment": f"Key Vault {keyvault} has been created.",
        "name": keyvault,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.vault.present(
        ctx,
        name=keyvault,
        resource_group=resource_group,
        location=location,
        tenant_id=tenant_id,
        sku=sku,
        access_policies=access_policies,
        enable_soft_delete=False,
    )
    # sleep because access policies need some time to take effect
    time.sleep(5)
    ret["changes"]["new"].pop("id")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, location, tags, keyvault):
    tenant_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("tenant")
    app_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("client_id")
    object_id = next(
        iter(
            await hub.exec.azurerm.graphrbac.service_principal.list(
                ctx, sp_filter=f"appId eq '{app_id}'"
            )
        )
    )
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
        "changes": {"tags": {"new": tags,},},
        "comment": f"Key Vault {keyvault} has been updated.",
        "name": keyvault,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.vault.present(
        ctx,
        name=keyvault,
        resource_group=resource_group,
        location=location,
        tenant_id=tenant_id,
        sku=sku,
        access_policies=access_policies,
        enable_soft_delete=False,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, location, tags, keyvault):
    subscription_id = (
        hub.acct.PROFILES["azurerm"].get("default", {}).get("subscription_id")
    )
    tenant_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("tenant")
    app_id = hub.acct.PROFILES["azurerm"].get("default", {}).get("client_id")
    object_id = next(
        iter(
            await hub.exec.azurerm.graphrbac.service_principal.list(
                ctx, sp_filter=f"appId eq '{app_id}'"
            )
        )
    )
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
                "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.KeyVault/vaults/{keyvault}",
                "location": location,
                "name": keyvault,
                "properties": {
                    "access_policies": access_policies,
                    "enable_soft_delete": False,
                    "enabled_for_deployment": False,
                    "enable_rbac_authorization": False,
                    "sku": {"family": "A", "name": "standard"},
                    "soft_delete_retention_in_days": 90,
                    "tenant_id": f"{tenant_id}",
                    "vault_uri": f"https://{keyvault}.vault.azure.net/",
                },
                "tags": tags,
                "type": "Microsoft.KeyVault/vaults",
            },
        },
        "comment": f"Key Vault {keyvault} has been deleted.",
        "name": keyvault,
        "result": True,
    }
    ret = await hub.states.azurerm.keyvault.vault.absent(ctx, keyvault, resource_group)
    assert ret == expected
