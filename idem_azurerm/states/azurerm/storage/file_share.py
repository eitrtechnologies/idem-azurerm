# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Storage File Share State Module

.. versionadded:: VERSION

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
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

log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.storage.account.present",
        ]
    }
}


async def present(
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
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: VERSION

    Ensure the specified file share exists within the specified storage account.

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

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure file share exists:
            azurerm.storage.file_share.present:
                - name: my_file_share
                - account_name: my_account
                - resource_group: my_rg

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

    share = await hub.exec.azurerm.storage.file_share.get(
        ctx, name, account_name, resource_group, **connection_auth
    )

    if "error" not in share:
        action = "update"

        if share_quota and shared_quota != share.get("share_quota"):
            ret["changes"]["share_quota"] = {
                "old": share.get("share_quota"),
                "new": share_quota,
            }

        if access_tier and access_tier != share.get("access_tier"):
            ret["changes"]["access_tier"] = {
                "old": share.get("access_tier"),
                "new": access_tier,
            }

        if metadata is not None:
            metadata_changes = differ.deep_diff(share.get("metadata", {}), metadata)
            if metadata_changes:
                ret["changes"]["metadata"] = metadata_changes

        if root_squash and root_squash != share.get("root_squash"):
            ret["changes"]["root_squash"] = {
                "old": share.get("root_squash"),
                "new": root_squash,
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "File share {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "File share {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "File share {0} would be created.".format(name)
        ret["result"] = None
        return ret

    account_kwargs = kwargs.copy()
    account_kwargs.update(connection_auth)

    if action == "create":
        share = await hub.exec.azurerm.storage.file_share.create(
            ctx=ctx,
            name=name,
            account_name=account_name,
            resource_group=resource_group,
            share_quota=share_quota,
            access_tier=access_tier,
            enabled_protocols=enabled_protocols,
            root_squash=root_squash,
            metadata=metadata,
            **share_kwargs,
        )
    else:
        share = await hub.exec.azurerm.storage.file_share.update(
            ctx=ctx,
            name=name,
            account_name=account_name,
            resource_group=resource_group,
            share_quota=share_quota,
            access_tier=access_tier,
            root_squash=root_squash,
            metadata=metadata,
            **share_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": share}

    if "error" not in share:
        ret["result"] = True
        ret["comment"] = f"File share {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} file share {1}! ({2})".format(
        action, name, share.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, account_name, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: VERSION

    Ensures the specified file share does not exist within the specified storage account.

    :param name: The name of the file share being deleted.

    :param account_name: The name of the storage account that the file share belongs to.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure file share does not exist:
            azurerm.storage.file_share.absent:
                - name: my_file_share
                - account_name: my_account
                - resource_group: my_rg

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

    share = await hub.exec.azurerm.storage.file_share.get(
        ctx, name, account_name, resource_group, **connection_auth
    )

    if "error" in share:
        ret["result"] = True
        ret["comment"] = "File share {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "File share {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": share,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.storage.file_share.delete(
        ctx, name, account_name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "File share {0} has been deleted.".format(name)
        ret["changes"] = {"old": share, "new": {}}
        return ret

    ret["comment"] = "Failed to delete file share {0}!".format(name)
    return ret
