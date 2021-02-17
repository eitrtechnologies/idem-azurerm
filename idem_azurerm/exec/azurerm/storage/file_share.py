# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Storage File Share Operations Execution Module

.. versionadded:: VERSION

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
    import azure.mgmt.storage  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create(
    hub,
    ctx,
    name,
    account_name,
    resource_group,
    access_tier=None,
    share_quota=None,
    enabled_protocols=None,
    root_squash=None,
    metadata=None,
    **kwargs,
):
    """
    .. versionadded:: VERSION

    Creates a new share under the specified account as described by request body. The share resource includes metadata
    and properties for that share. It does not include a list of the files contained by the share.

    :param name: The name of the file share within the specified storage account. File share names must be between 3
        and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-) character
        must be immediately preceded and followed by a letter or number.

    :param account_name: The name of the storage account within the specified resource group. Storage account names
        must be between 3 and 24 characters in length and use numbers and lower- case letters only.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param access_tier: The access tier for specific share. A GpV2 Storage account can choose between
        "TransactionOptimized" (which is the default value), "Hot", and "Cool". A FileStorage storage account can
        choose "Premium". Possible values include: "TransactionOptimized", "Hot", "Cool", "Premium".

    :param share_quota: Set a quota in GiB, up to 5120 GiB, to limit the total size of files on the share.
        This is an integer value.

    :param enabled_protocols: The authentication protocol that is used for the file share. Can only be specified when
        creating a share. Possible values include: "SMB", "NFS".

    :param root_squash: The property is for NFS share only. The default is "NoRootSquash". Possible values
        include: "NoRootSquash", "RootSquash", "AllSquash".

    :param metadata: A name-value pair to associate with the share as metadata.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.file_share.create test_name test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        sharemodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "FileShare",
            share_quota=share_quota,
            access_tier=access_tier,
            enabled_protocols=enabled_protocols,
            root_squash=root_squash,
            metadata=metadata,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        share = storconn.file_shares.create(
            share_name=name,
            account_name=account_name,
            resource_group_name=resource_group,
            file_share=sharemodel,
        )

        result = share.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, account_name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Deletes specified share under its account.

    :param name: The name of the file share to delete.

    :param account_name: The name of the storage account within the specified resource group.

    :param resource_group: The name of the resource group that the specified storage account for the file share
        belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.file_share.delete test_name test_account test_group

    """
    result = False
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        account = storconn.file_shares.delete(
            share_name=name,
            account_name=account_name,
            resource_group_name=resource_group,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, account_name, resource_group, expand="stats", **kwargs):
    """
    .. versionadded:: VERSION

    Gets properties of a specified share.

    :param name: The name of the file share within the specified storage account.

    :param account_name: The name of the storage account within the specified resource group.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param expand: An optional parameter used to expand the returned properties for the share. Defaults to "stats".

    CLI Example:

    .. code-block:: bash

        azurerm.storage.file_share.get test_name test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        share = storconn.file_shares.get(
            share_name=name,
            account_name=account_name,
            resource_group_name=resource_group,
            expand=expand,
        )

        result = share.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, account_name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Lists all file shares within the specified storage account.

    :param account_name: The name of the storage account within the specified resource group.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.file_share.list test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        shares = await hub.exec.azurerm.utils.paged_object_to_list(
            storconn.file_shares.list(
                account_name=account_name, resource_group_name=resource_group
            )
        )

        for share in shares:
            result[share["name"]] = share
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update(
    hub,
    ctx,
    name,
    account_name,
    resource_group,
    access_tier=None,
    share_quota=None,
    root_squash=None,
    metadata=None,
    **kwargs,
):
    """
    .. versionadded:: VERSION

    Updates share properties as specified in request body. Properties not mentioned in the request will not be changed.
    Update fails if the specified share does not already exist.

    :param name: The name of the file share within the specified storage account. File share names must be between 3
        and 63 characters in length and use numbers, lower-case letters and dash (-) only. Every dash (-) character
        must be immediately preceded and followed by a letter or number.

    :param account_name: The name of the storage account within the specified resource group. Storage account names
        must be between 3 and 24 characters in length and use numbers and lower- case letters only.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param access_tier: The access tier for specific share. A GpV2 Storage account can choose between
        "TransactionOptimized" (which is the default value), "Hot", and "Cool". A FileStorage storage account can
        choose "Premium". Possible values include: "TransactionOptimized", "Hot", "Cool", "Premium".

    :param share_quota: Set a quota in GiB, up to 5120 GiB, to limit the total size of files on the share.
        This is an integer value.

    :param root_squash: The property is for NFS share only. The default is "NoRootSquash". Possible values
        include: "NoRootSquash", "RootSquash", "AllSquash".

    :param metadata: A name-value pair to associate with the share as metadata.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.file_share.update test_name test_account test_group

    """
    result = {}
    storconn = await hub.exec.azurerm.utils.get_client(ctx, "storage", **kwargs)

    try:
        sharemodel = await hub.exec.azurerm.utils.create_object_model(
            "storage",
            "FileShare",
            share_quota=share_quota,
            access_tier=access_tier,
            root_squash=root_squash,
            metadata=metadata,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        share = storconn.file_shares.update(
            share_name=name,
            account_name=account_name,
            resource_group_name=resource_group,
            file_share=sharemodel,
        )

        result = share.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("storage", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
