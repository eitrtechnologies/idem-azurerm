# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Key Vault State Module

.. versionadded:: 2.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed via acct. Note that the
    authentication parameters are case sensitive.

    Required provider parameters:

    if using username and password:
      * ``subscription_id``
      * ``username``
      * ``password``

    if using a service principal:
      * ``subscription_id``
      * ``tenant``
      * ``client_id``
      * ``secret``

    Optional provider parameters:

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud. Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

    Example acct setup for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            default:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass

    The authentication parameters can also be passed as a dictionary of keyword arguments to the ``connection_auth``
    parameter of each state, but this is not preferred and could be deprecated in the future.

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging
from operator import itemgetter

log = logging.getLogger(__name__)

TREQ = {"present": {"require": ["states.azurerm.resource.group.present",]}}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    location,
    tenant_id,
    sku,
    access_policies=None,
    vault_uri=None,
    create_mode=None,
    enable_soft_delete=None,
    enable_purge_protection=None,
    enabled_for_deployment=None,
    enabled_for_disk_encryption=None,
    enabled_for_template_deployment=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a specified keyvault exists.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the vault belongs.

    :param location: The supported Azure location where the key vault should be created.

    :param tenant_id: The Azure Active Direction tenant ID that should be used for authenticating requests to
        the key vault.

    :param sku: The SKU name to specify whether the key vault is a standard vault or a premium vault. Possible
        values include: 'standard' and 'premium'.

    :param access_policies: A list of 0 to 16 dictionaries that represent AccessPolicyEntry objects. The
        AccessPolicyEntry objects represent identities that have access to the key vault. All identities in the
        list must use the same tenant ID as the key vault's tenant ID. When createMode is set to recover, access
        policies are not required. Otherwise, access policies are required. Valid parameters are:
        - ``tenant_id``: Required. The Azure Active Directory tenant ID that should be used for authenticating
          requests to the key vault.
        - ``object_id``: Required. The object ID of a user, service principal, or security group in the Azure Active
          Directory tenant for the vault. The object ID must be unique for the list of access policies.
        - ``permissions``: Required. A dictionary representing permissions the identity has for keys, secrets, and
          certifications. Valid parameters include:
            - ``keys``: A list that represents permissions to keys. Possible values include: 'backup', 'create',
              'decrypt', 'delete', 'encrypt', 'get', 'import_enum', 'list', 'purge', 'recover', 'restore', 'sign',
              'unwrap_key', 'update', 'verify', and 'wrap_key'.
            - ``secrets``: A list that represents permissions to secrets. Possible values include: 'backup', 'delete',
              'get', 'list', 'purge', 'recover', 'restore', and 'set'.
            - ``certificates``: A list that represents permissions to certificates. Possible values include: 'create',
              'delete', 'deleteissuers', 'get', 'getissuers', 'import_enum', 'list', 'listissuers', 'managecontacts',
              'manageissuers', 'purge', 'recover', 'setissuers', and 'update'.
            - ``storage``: A list that represents permissions to storage accounts. Possible values include: 'backup',
              'delete', 'deletesas', 'get', 'getsas', 'list', 'listsas', 'purge', 'recover', 'regeneratekey',
              'restore', 'set', 'setsas', and 'update'.

    :param vault_uri: The URI of the vault for performing operations on keys and secrets.

    :param create_mode: The vault's create mode to indicate whether the vault needs to be recovered or not. Possible
        values include: 'recover' and 'default'.

    :param enable_soft_delete: A boolean value specifying whether recoverable deletion is enabled for this key vault.
        Setting this property to true activates the soft delete feature, whereby vaults or vault entities can be
        recovered after deletion. Enabling this functionality is irreversible - that is, the property does not accept
        false as its value. Defaults to False.

    :param enable_purge_protection: A boolean value specifying whether protection against purge is enabled for this
        vault. Setting this property to true activates protection against purge for this vault and its content - only
        the Key Vault service may initiate a hard, irrecoverable deletion. The setting is effective only if soft
        delete is also enabled. Enabling this functionality is irreversible - that is, the property does not accept
        false as its value.

    :param enabled_for_deployment: A boolean value specifying whether Azure Virtual Machines are permitted to
        retrieve certificates stored as secrets from the key vault. Defaults to False.

    :param enabled_for_disk_encryption: A boolean value specifying whether Azure Disk Encrpytion is permitted to
        retrieve secrets from the vault and unwrap keys. Defaults to False.

    :param enabled_for_template_deployment: A boolean value specifying whether Azure Resource Manager is permitted
        to retrieve secrets from the key vault. Defaults to False.

    :param tags: A dictionary of strings can be passed as tag metadata to the key vault.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key vault exists:
            azurerm.keyvault.vault.present:
                - name: my_vault
                - resource_group: my_rg
                - location: my_location
                - tenant_id: my_tenant
                - sku: my_sku
                - access_policies:
                  - tenant_id: my_tenant
                    object_id: my_object
                    permissions:
                      keys:
                        - perm1
                        - perm2
                        - perm3
                      secrets:
                        - perm1
                        - perm2
                        - perm3
                      certificates:
                        - perm1
                        - perm2
                        - perm3
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    vault = await hub.exec.azurerm.keyvault.vault.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in vault:
        action = "update"
        tag_changes = differ.deep_diff(vault.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # Checks for changes in the account_policies parameter
        if len(access_policies or []) == len(
            vault.get("properties").get("access_policies", [])
        ):
            new_policies_sorted = sorted(
                access_policies or [], key=itemgetter("object_id")
            )
            old_policies_sorted = sorted(
                vault.get("properties").get("access_policies", []),
                key=itemgetter("object_id"),
            )
            changed = False

            for index, new_policy in enumerate(new_policies_sorted):
                old_policy = old_policies_sorted[index]

                # Checks for changes with the tenant_id key
                if old_policy.get("tenant_id") != new_policy.get("tenant_id"):
                    changed = True
                    break

                # Checks for changes with the object_id key
                if old_policy.get("object_id") != new_policy.get("object_id"):
                    changed = True
                    break

                # Checks for changes within the permissions key
                if new_policy["permissions"].get("keys") is not None:
                    new_keys = sorted(new_policy["permissions"].get("keys"))
                    old_keys = sorted(old_policy["permissions"].get("keys", []))
                    if new_keys != old_keys:
                        changed = True
                        break

                if new_policy["permissions"].get("secrets") is not None:
                    new_secrets = sorted(new_policy["permissions"].get("secrets"))
                    old_secrets = sorted(old_policy["permissions"].get("secrets", []))
                    if new_secrets != old_secrets:
                        changed = True
                        break

                if new_policy["permissions"].get("certificates") is not None:
                    new_certificates = sorted(
                        new_policy["permissions"].get("certificates")
                    )
                    old_certificates = sorted(
                        old_policy["permissions"].get("certificates", [])
                    )
                    if new_certificates != old_certificates:
                        changed = True
                        break

            if changed:
                ret["changes"]["access_policies"] = {
                    "old": vault.get("properties").get("access_policies", []),
                    "new": access_policies,
                }

        else:
            ret["changes"]["access_policies"] = {
                "old": vault.get("properties").get("access_policies", []),
                "new": access_policies,
            }

        if sku != vault.get("properties").get("sku").get("name"):
            ret["changes"]["sku"] = {
                "old": vault.get("properties").get("sku").get("name"),
                "new": sku,
            }

        if enabled_for_deployment is not None:
            if enabled_for_deployment != vault.get("properties").get(
                "enabled_for_deployment"
            ):
                ret["changes"]["enabled_for_deployment"] = {
                    "old": vault.get("properties").get("enabled_for_deployment"),
                    "new": enabled_for_deployment,
                }

        if enabled_for_disk_encryption is not None:
            if enabled_for_disk_encryption != vault.get("properties").get(
                "enabled_for_disk_encryption"
            ):
                ret["changes"]["enabled_for_disk_encryption"] = {
                    "old": vault.get("properties").get("enabled_for_disk_encryption"),
                    "new": enabled_for_disk_encryption,
                }

        if enabled_for_template_deployment is not None:
            if enabled_for_template_deployment != vault.get("properties").get(
                "enabled_for_template_deployment"
            ):
                ret["changes"]["enabled_for_template_deployment"] = {
                    "old": vault.get("properties").get(
                        "enabled_for_template_deployment"
                    ),
                    "new": enabled_for_template_deployment,
                }

        if enable_soft_delete is not None:
            if enable_soft_delete != vault.get("properties").get("enable_soft_delete"):
                ret["changes"]["enable_soft_delete"] = {
                    "old": vault.get("properties").get("enable_soft_delete"),
                    "new": enable_soft_delete,
                }

        if enable_purge_protection is not None:
            if enable_purge_protection != vault.get("properties").get(
                "enable_purge_protection"
            ):
                ret["changes"]["enable_purge_protection"] = {
                    "old": vault.get("properties").get("enable_purge_protection"),
                    "new": enable_purge_protection,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Key Vault {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Key Vault {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "location": location,
                "tenant_id": tenant_id,
                "sku": sku,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if access_policies:
            ret["changes"]["new"]["access_policies"] = access_policies
        if vault_uri:
            ret["changes"]["new"]["vault_uri"] = vault_uri
        if enabled_for_deployment is not None:
            ret["changes"]["new"]["enabled_for_deployment"] = enabled_for_deployment
        if enabled_for_disk_encryption is not None:
            ret["changes"]["new"][
                "enabled_for_disk_encryption"
            ] = enabled_for_disk_encryption
        if enabled_for_template_deployment is not None:
            ret["changes"]["new"][
                "enabled_for_template_deployment"
            ] = enabled_for_template_deployment
        if enable_soft_delete is not None:
            ret["changes"]["new"]["enable_soft_delete"] = enable_soft_delete
        if create_mode:
            ret["changes"]["new"]["create_mode"] = create_mode
        if enable_purge_protection is not None:
            ret["changes"]["new"]["enable_purge_protection"] = enable_purge_protection

    if ctx["test"]:
        ret["comment"] = "Key vault {0} would be created.".format(name)
        ret["result"] = None
        return ret

    vault_kwargs = kwargs.copy()
    vault_kwargs.update(connection_auth)

    vault = await hub.exec.azurerm.keyvault.vault.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        location=location,
        tenant_id=tenant_id,
        sku=sku,
        access_policies=access_policies,
        vault_uri=vault_uri,
        create_mode=create_mode,
        enable_soft_delete=enable_soft_delete,
        enable_purge_protection=enable_purge_protection,
        enabled_for_deployment=enabled_for_deployment,
        enabled_for_disk_encryption=enabled_for_disk_encryption,
        enabled_for_template_deployment=enabled_for_template_deployment,
        tags=tags,
        **vault_kwargs,
    )

    if "error" not in vault:
        ret["result"] = True
        ret["comment"] = f"Key Vault {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Key Vault {1}! ({2})".format(
        action, name, vault.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a specified key vault does not exist.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the vault belongs.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key vault is absent:
            azurerm.keyvault.vault.absent:
                - name: my_vault
                - resource_group: my_rg
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    vault = await hub.exec.azurerm.keyvault.vault.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in vault:
        ret["result"] = True
        ret["comment"] = "Key Vault {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Key Vault {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": vault,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.keyvault.vault.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Key Vault {0} has been deleted.".format(name)
        ret["changes"] = {"old": vault, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Key Vault {0}!".format(name)
    return ret
