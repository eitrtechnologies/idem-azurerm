# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Key Vault Execution Module

.. versionadded:: 2.0.0

.. versionchanged:: 4.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function or via acct in order to work properly.

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

"""
# Python libs
from __future__ import absolute_import
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.keyvault.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def check_name_availability(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 2.0.0

    Checks that the vault name is valid and is not already in use.

    :param name: The vault name.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.check_name_availability test_name

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        avail = vconn.vaults.check_name_availability(name=name,)

        result = avail.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(
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
    enabled_for_deployment=None,
    enabled_for_disk_encryption=None,
    enabled_for_template_deployment=None,
    enable_soft_delete=None,
    soft_delete_retention=None,
    enable_purge_protection=None,
    enable_rbac_authorization=None,
    network_acls=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Create or update a key vault in the specified subscription.

    :param name: The vault name.

    :param resource_group: The name of the resource group to which the vault belongs.

    :param location: The supported Azure location where the key vault should be created.

    :param tenant_id: The Azure Active Direction tenant ID that should be used for authenticating requests to
        the key vault.

    :param sku: The SKU name to specify whether the key vault is a standard vault or a premium vault. Possible
        values include: 'standard' and 'premium'.

    :param access_policies: A list of 0 to 16 dictionaries that represent AccessPolicyEntry objects. The
        AccessPolicyEntry objects represent identities that have access to the key vault. All identities in the
        list must use the same tenant ID as the key vault's tenant ID. When createMode is set to "recover", access
        policies are not required. Otherwise, access policies are required. Valid parameters are:

        - ``tenant_id``: (Required) The Azure Active Directory tenant ID that should be used for authenticating
          requests to the key vault.
        - ``object_id``: (Required) The object ID of a user, service principal, or security group in the Azure Active
          Directory tenant for the vault. The object ID must be unique for the list of access policies.
        - ``application_id``: (Optional) Application ID of the client making request on behalf of a principal.
        - ``permissions``: (Required) A dictionary representing permissions the identity has for keys, secrets, and
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

    :param create_mode: The vault's create mode to indicate whether the vault needs to be recovered or not.
        Possible values include: 'recover' and 'default'.

    :param enabled_for_deployment: A boolean value specifying whether Azure Virtual Machines are permitted to
        retrieve certificates stored as secrets from the key vault.

    :param enabled_for_disk_encryption: A boolean value specifying whether Azure Disk Encrpytion is permitted
        to retrieve secrets from the vault and unwrap keys.

    :param enabled_for_template_deployment: A boolean value specifying whether Azure Resource Manager is
        permitted to retrieve secrets from the key vault.

    :param create_mode: The vault's create mode to indicate whether the vault needs to be recovered or not.
        Possible values include: 'recover' and 'default'.

    :param enable_soft_delete: A boolean value that specifies whether the 'soft delete' functionality is
        enabled for this key vault. If it's not set to any value (True or False) when creating new key vault, it will
        be set to True by default. Once set to True, it cannot be reverted to False.

    :param soft_delete_retention: The soft delete data retention period in days. It accepts values between
        7-90, inclusive. Default value is 90.

    :param enable_purge_protection: A boolean value specifying whether protection against purge is enabled for this
        vault. Setting this property to True activates protection against purge for this vault and its content - only
        the Key Vault service may initiate a hard, irrecoverable deletion. Enabling this functionality is irreversible,
        that is, the property does not accept False as its value. This is only effective if soft delete has been
        enabled via the ``enable_soft_delete`` parameter.

    :param enable_rbac_authorization: A boolean value that controls how data actions are authorized. When set to True,
        the key vault will use Role Based Access Control (RBAC) for authorization of data actions, and the access
        policies specified in vault properties will be ignored (warning: this is a preview feature). When set as
        False, the key vault will use the access policies specified in vault properties, and any policy stored on Azure
        Resource Manager will be ignored. Note that management actions are always authorized with RBAC. Defaults
        to False.

    :param network_acls: A dictionary representing a NetworkRuleSet. Rules governing the accessibility of
        the key vault from specific network locations.

    :param tags: The tags that will be assigned to the key vault.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.create_or_update test_name test_rg test_location test_tenant test_sku test_policies

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    sku = {"name": sku}

    if not access_policies:
        access_policies = []

    # Create the VaultProperties object
    try:
        propsmodel = await hub.exec.azurerm.utils.create_object_model(
            "keyvault",
            "VaultProperties",
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
            soft_delete_retention_in_days=soft_delete_retention,
            enable_rbac_authorization=enable_rbac_authorization,
            network_acls=network_acls,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    # Create the VaultCreateOrUpdateParameters object
    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "keyvault",
            "VaultCreateOrUpdateParameters",
            location=location,
            properties=propsmodel,
            tags=tags,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        vault = vconn.vaults.create_or_update(
            vault_name=name, resource_group_name=resource_group, parameters=paramsmodel
        )

        vault.wait()
        result = vault.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes the specified Azure key vault.

    :param name: The vault name.

    :param resource_group: The name of the resource group to which the vault belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.delete test_name test_rg

    """
    result = False
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        vault = vconn.vaults.delete(vault_name=name, resource_group_name=resource_group)

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets the specified Azure key vault.

    :param name: The vault name.

    :param resource_group: The name of the resource group to which the vault belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.get test_name test_rg

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        vault = vconn.vaults.get(vault_name=name, resource_group_name=resource_group)

        result = vault.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_deleted(hub, ctx, name, location, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets the deleted Azure key vault.

    :param name: The vault name.

    :param location: The location of the deleted vault.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.get_deleted test_name test_location

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        vault = vconn.vaults.get_deleted(vault_name=name, location=location)

        result = vault.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, top=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Gets information about the vaults associated with the subscription.

    :param resource_group: The name of the resource group to limit the results.

    :param top: Maximum number of results to return.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.list

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        if resource_group:
            vaults = await hub.exec.azurerm.utils.paged_object_to_list(
                vconn.vaults.list_by_resource_group(
                    resource_group_name=resource_group, top=top
                )
            )
        else:
            vaults = await hub.exec.azurerm.utils.paged_object_to_list(
                vconn.vaults.list(top=top)
            )

        for vault in vaults:
            result[vault["name"]] = vault
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_subscription(hub, ctx, top=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    The List operation gets information about the vaults associated with the subscription.

    :param top: Maximum number of results to return.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.list_by_subscription

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        vaults = await hub.exec.azurerm.utils.paged_object_to_list(
            vconn.vaults.list_by_subscription(top=top)
        )

        for vault in vaults:
            result[vault["name"]] = vault
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_deleted(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets information about the deleted vaults in a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.list_deleted

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        vaults = await hub.exec.azurerm.utils.paged_object_to_list(
            vconn.vaults.list_deleted()
        )

        for vault in vaults:
            result[vault["name"]] = vault
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def purge_deleted(hub, ctx, name, location, **kwargs):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Permanently deletes (purges) the specified Azure key vault.

    :param name: The name of the soft-deleted vault.

    :param location: The location of the soft-deleted vault.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.purge_deleted test_name test_location

    """
    result = False
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    try:
        vault = vconn.vaults.purge_deleted(vault_name=name, location=location)

        vault.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)

    return result


async def update_access_policy(
    hub, ctx, name, resource_group, operation_kind, access_policies, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Update access policies in a key vault in the specified subscription.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the server belongs.

    :param operation_kind: Name of the operation. Possible values include: 'add', 'replace', and 'remove'.

    :param access_policies: A list of 0 to 16 dictionaries that represent AccessPolicyEntry objects. The
        AccessPolicyEntry objects represent identities that have access to the key vault. All identities in the
        list must use the same tenant ID as the key vault's tenant ID. When createMode is set to "recover", access
        policies are not required. Otherwise, access policies are required. Valid parameters are:

        - ``tenant_id``: (Required) The Azure Active Directory tenant ID that should be used for authenticating
          requests to the key vault.
        - ``object_id``: (Required) The object ID of a user, service principal, or security group in the Azure Active
          Directory tenant for the vault. The object ID must be unique for the list of access policies.
        - ``application_id``: (Optional) Application ID of the client making request on behalf of a principal.
        - ``permissions``: (Required) A dictionary representing permissions the identity has for keys, secrets, and
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

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.vault.update_access_policy test_name test_rg test_kind test_policies

    """
    result = {}
    vconn = await hub.exec.azurerm.utils.get_client(ctx, "keyvault", **kwargs)

    # Create the VaultAccessPolicyProperties object
    try:
        propsmodel = await hub.exec.azurerm.utils.create_object_model(
            "keyvault",
            "VaultAccessPolicyProperties",
            access_policies=access_policies,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        vault = vconn.vaults.update_access_policy(
            vault_name=name,
            resource_group_name=resource_group,
            operation_kind=operation_kind,
            properties=propsmodel,
        )

        result = vault.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("keyvault", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
