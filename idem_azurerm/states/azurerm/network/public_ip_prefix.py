# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Public IP Prefix State Module

.. versionadded:: 4.0.0

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
    "present": {"require": ["states.azurerm.resource.group.present"]},
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    prefix_length=None,
    sku="standard",
    public_ip_address_version="IPv4",
    zones=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Ensure a public IP prefix exists.

    :param name: The name of the public IP prefix.

    :param resource_group: The resource group of the public IP prefix.

    :param prefix_length: An integer representing the length of the Public IP Prefix. This value is immutable
        once set. If the value of the ``public_ip_address_version`` parameter is "IPv4", then possible values include
        28, 29, 30, 31. If the value of the ``public_ip_address_version`` parameter is "IPv6", then possible values
        include 124, 125, 126, 127.

    :param sku: The name of a public IP prefix SKU. Possible values include: "standard". Defaults to "standard".

    :param public_ip_address_version: The public IP address version. Possible values include: "IPv4" and "IPv6".
        Defaults to "IPv4".

    :param zones: A list of availability zones that denotes where the IP allocated for the resource needs
        to come from.

    :param tags: A dictionary of strings can be passed as tag metadata to the public IP prefix object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure public IP prefix exists:
            azurerm.network.public_ip_prefix.present:
                - name: test_prefix
                - resource_group: test_group
                - prefix_length: 28
                - sku: "standard"
                - public_ip_version: "IPv4"
                - tags:
                    contact_name: Elmer Fudd Gantry

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

    prefix = await hub.exec.azurerm.network.public_ip_prefix.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in prefix:
        action = "update"

        # tag changes
        tag_changes = differ.deep_diff(prefix.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # public_ip_address_version changes
        if public_ip_address_version:
            if (
                public_ip_address_version.lower()
                != prefix.get("public_ip_address_version", "").lower()
            ):
                ret["changes"]["public_ip_address_version"] = {
                    "old": prefix.get("public_ip_address_version"),
                    "new": public_ip_address_version,
                }

        # zones changes
        if zones is not None:
            if zones.sort() != prefix.get("zones").sort():
                ret["changes"]["zones"] = {"old": prefix.get("zones"), "new": zones}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Public IP prefix {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Public IP prefix {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Public IP prefix {0} would be created.".format(name)
        ret["result"] = None
        return ret

    prefix_kwargs = kwargs.copy()
    prefix_kwargs.update(connection_auth)

    if action == "create" or len(ret["changes"]) > 1 or not tag_changes:
        prefix = await hub.exec.azurerm.network.public_ip_prefix.create_or_update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            prefix_length=prefix_length,
            sku=sku,
            tags=tags,
            public_ip_address_version=public_ip_address_version,
            zones=zones,
            **prefix_kwargs,
        )

    # no idea why create_or_update doesn't work for tags
    if action == "update" and tag_changes:
        prefix = await hub.exec.azurerm.network.public_ip_prefix.update_tags(
            ctx, name=name, resource_group=resource_group, tags=tags, **prefix_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": prefix}

    if "error" not in prefix:
        ret["result"] = True
        ret["comment"] = f"Public IP prefix {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} public IP prefix {1}! ({2})".format(
        action, name, prefix.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Ensure a public IP prefix does not exist in the resource group.

    :param name: The name of the public IP prefix.

    :param resource_group: The resource group assigned to the public IP prefix.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure public ip prefix absent:
            azurerm.network.public_ip_prefix.absent:
              - name: test_lb
              - resource_group: test_group

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

    prefix = await hub.exec.azurerm.network.public_ip_prefix.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in prefix:
        ret["result"] = True
        ret["comment"] = "Public IP prefix {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Public IP prefix {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": prefix,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.public_ip_prefix.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Public IP prefix {0} has been deleted.".format(name)
        ret["changes"] = {"old": prefix, "new": {}}
        return ret

    ret["comment"] = "Failed to delete public IP prefix {0}!".format(name)
    return ret
