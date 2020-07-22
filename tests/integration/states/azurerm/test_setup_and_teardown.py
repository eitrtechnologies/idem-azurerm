import pytest
import string
import random


@pytest.mark.run(order=2)
@pytest.mark.asyncio
# This setup function deploys the following to use within tests:
# - 2 Virtual Networks
# - 1 Subnet
# - 1 Public IP Address
# - 1 Network Interface
# - 1 Keyvault
# - 1 Key
async def test_setup(
    hub,
    ctx,
    vnet,
    vnet2,
    subnet,
    public_ip_addr,
    network_interface,
    resource_group,
    ip_config,
    key,
    keyvault,
):
    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx, name=vnet, resource_group=resource_group, address_prefixes=["172.0.0.0/8"],
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.present(
        ctx, name=vnet2, resource_group=resource_group, address_prefixes=["10.0.0.0/8"],
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.subnet_present(
        ctx,
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix="172.0.0.0/16",
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=[{"service": "Microsoft.sql"}],
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.public_ip_address.present(
        ctx, name=public_ip_addr, resource_group=resource_group,
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.network_interface.present(
        ctx,
        name=network_interface,
        resource_group=resource_group,
        subnet=subnet,
        virtual_network=vnet,
        ip_configurations=[{"name": ip_config}],
    )
    assert ret["result"] == True

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

    ret = await hub.states.azurerm.keyvault.vault.present(
        ctx,
        name=keyvault,
        resource_group=resource_group,
        access_policies=access_policies,
        tenant_id=tenant_id,
        sku=sku,
        location="eastus",
    )
    assert ret["result"] == True


@pytest.mark.run(order=-2)
@pytest.mark.asyncio
async def test_teardown(
    hub,
    ctx,
    vnet,
    vnet2,
    subnet,
    public_ip_addr,
    network_interface,
    resource_group,
    keyvault,
):
    ret = await hub.states.azurerm.network.network_interface.absent(
        ctx, name=network_interface, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.subnet_absent(
        ctx, name=subnet, virtual_network=vnet, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, name=vnet, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.virtual_network.absent(
        ctx, name=vnet2, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.network.public_ip_address.absent(
        ctx, name=public_ip_addr, resource_group=resource_group
    )
    assert ret["result"] == True

    ret = await hub.states.azurerm.keyvault.vault.absent(
        ctx, name=keyvault, resource_group=resource_group
    )
    assert ret["result"] == True
