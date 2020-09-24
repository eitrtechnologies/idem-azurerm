# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Group State Module

.. versionadded:: 1.0.0

.. versionchanged:: 4.0.0

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

    Example configuration for Azure Resource Manager authentication:

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
# Import Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging

log = logging.getLogger(__name__)


async def present(
    hub, ctx, name, location, managed_by=None, tags=None, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a resource group exists.

    :param name:
        Name of the resource group.

    :param location:
        The Azure location in which to create the resource group. This value cannot be updated once
        the resource group is created.

    :param managed_by:
        The ID of the resource that manages this resource group. This value cannot be updated once the
        resource group is created.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the resource group object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure resource group exists:
            azurerm.resource.group.present:
                - name: group1
                - location: eastus
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

    group = await hub.exec.azurerm.resource.group.get(
        ctx, name, azurerm_log_level="info", **connection_auth
    )

    if "error" not in group:
        action = "update"

        # tag changes
        tag_changes = differ.deep_diff(group.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Resource group {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["comment"] = "Resource group {0} tags would be updated.".format(name)
            ret["result"] = None
            ret["changes"] = {"old": group.get("tags", {}), "new": tags}
            return ret

    elif ctx["test"]:
        ret["comment"] = "Resource group {0} would be created.".format(name)
        ret["result"] = None
        return ret

    group_kwargs = kwargs.copy()
    group_kwargs.update(connection_auth)

    group = await hub.exec.azurerm.resource.group.create_or_update(
        ctx, name, location, managed_by=managed_by, tags=tags, **group_kwargs
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": group}

    if "error" not in group:
        ret["result"] = True
        ret["comment"] = f"Resource group {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} resource group {1}! ({2})".format(
        action, name, group.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a resource group does not exist in the current subscription.

    :param name:
        Name of the resource group.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure resource group absent:
            azurerm.resource.group.absent:
              - name: test_group

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

    group = await hub.exec.azurerm.resource.group.get(
        ctx, name, azurerm_log_level="info", **connection_auth
    )

    if "error" in group:
        ret["result"] = True
        ret["comment"] = "Resource group {0} is already absent.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Resource group {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": group,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.resource.group.delete(ctx, name, **connection_auth)

    if deleted:
        ret["result"] = True
        ret["comment"] = "Resource group {0} has been deleted.".format(name)
        ret["changes"] = {"old": group, "new": {}}
        return ret

    ret["comment"] = "Failed to delete resource group {0}!".format(name)
    return ret
