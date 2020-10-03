# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Proximity Placement Group State Module

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
    "present": {"require": ["states.azurerm.resource.group.present",]},
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    group_type="standard",
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Ensures the specified proximity placement group exists.

    :param name: The name of the proximity placement group.

    :param resource_group: The name of the resource group.

    :param group_type: The type of the proximity placement group. Possible values include: "standard", "ultra".
        Defaults to "standard".

    :param tags: A dictionary of strings can be passed as tag metadata to the proximity placement group object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure proximity placement group exists:
            azurerm.compute.proximity_placement_group.present:
                - name: test_ppg
                - resource_group: test_group
                - group_type: test_type
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

    ppg = await hub.exec.azurerm.compute.proximity_placement_group.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in ppg:
        action = "update"

        tag_changes = differ.deep_diff(ppg.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Proximity placement group {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Proximity placement group {0} would be updated.".format(
                name
            )
            return ret

    if ctx["test"]:
        ret["comment"] = "Proximity placement group {0} would be created.".format(name)
        ret["result"] = None
        return ret

    ppg_kwargs = kwargs.copy()
    ppg_kwargs.update(connection_auth)

    ppg = await hub.exec.azurerm.compute.proximity_placement_group.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        group_type=group_type,
        tags=tags,
        **ppg_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": ppg}

    if "error" not in ppg:
        ret["result"] = True
        ret["comment"] = f"Proximity placement group {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} proximity placement group {1}! ({2})".format(
        action, name, ppg.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Ensures the specified proximity placement group does not exist.

    :param name: The name of the proximity placement group.

    :param resource_group: The name of the resource group.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure proximity placement group absent:
            azurerm.compute.proximity_placement_group.absent:
                - name: test_ppg
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

    ppg = await hub.exec.azurerm.compute.proximity_placement_group.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in ppg:
        ret["result"] = True
        ret["comment"] = "Proximity placement group {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Proximity placement group {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": ppg,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.compute.proximity_placement_group.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Proximity placement group {0} has been deleted.".format(name)
        ret["changes"] = {"old": ppg, "new": {}}
        return ret

    ret["comment"] = "Failed to delete proximity placement group {0}!".format(name)
    return ret
