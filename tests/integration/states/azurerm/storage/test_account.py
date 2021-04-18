import pytest


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_present(hub, ctx, resource_group, location, storage_account):
    sku = "Standard_LRS"
    kind = "StorageV2"
    expected = {
        "changes": {
            "new": {
                "name": storage_account,
                "location": location,
                "primary_location": location,
                "kind": kind,
                "sku": {"name": sku, "tier": "Standard"},
                "tags": {},
                "type": "Microsoft.Storage/storageAccounts",
                "status_of_primary": "available",
                "access_tier": "Hot",
                "private_endpoint_connections": [],
                "provisioning_state": "Succeeded",
                "primary_endpoints": {
                    "blob": f"https://{storage_account}.blob.core.windows.net/",
                    "dfs": f"https://{storage_account}.dfs.core.windows.net/",
                    "file": f"https://{storage_account}.file.core.windows.net/",
                    "queue": f"https://{storage_account}.queue.core.windows.net/",
                    "table": f"https://{storage_account}.table.core.windows.net/",
                    "web": f"https://{storage_account}.z13.web.core.windows.net/",
                },
                "network_rule_set": {
                    "bypass": "AzureServices",
                    "default_action": "Allow",
                    "ip_rules": [],
                    "virtual_network_rules": [],
                },
                "enable_https_traffic_only": True,
                "encryption": {
                    "key_source": "Microsoft.Storage",
                    "services": {
                        "blob": {
                            "enabled": True,
                            "key_type": "Account",
                        },
                        "file": {
                            "enabled": True,
                            "key_type": "Account",
                        },
                    },
                },
            },
            "old": {},
        },
        "comment": f"Storage account {storage_account} has been created.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.present(
        ctx,
        name=storage_account,
        resource_group=resource_group,
        location=location,
        kind=kind,
        sku=sku,
    )
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("creation_time")
    ret["changes"]["new"]["encryption"]["services"]["blob"].pop("last_enabled_time")
    ret["changes"]["new"]["encryption"]["services"]["file"].pop("last_enabled_time")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
@pytest.mark.asyncio
async def test_changes(hub, ctx, resource_group, tags, location, storage_account):
    sku = "Standard_LRS"
    kind = "StorageV2"
    expected = {
        "changes": {
            "tags": {
                "new": tags,
            },
        },
        "comment": f"Storage account {storage_account} has been updated.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.present(
        ctx,
        name=storage_account,
        resource_group=resource_group,
        location=location,
        sku=sku,
        kind=kind,
        tags=tags,
    )
    assert ret == expected


@pytest.mark.run(order=-3)
@pytest.mark.asyncio
async def test_absent(hub, ctx, resource_group, storage_account):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": storage_account,
            },
        },
        "comment": f"Storage account {storage_account} has been deleted.",
        "name": storage_account,
        "result": True,
    }
    ret = await hub.states.azurerm.storage.account.absent(
        ctx, storage_account, resource_group
    )
    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
