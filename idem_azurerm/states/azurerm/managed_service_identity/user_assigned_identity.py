# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) MSI User Assigned Identity State Module

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
    hub, ctx, name, resource_group, tags=None, connection_auth=None, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Ensure the specified user assigned identity exists.

    :param name: The name of the user assigned identity..

    :param resource_group: The resource group assigned to the user assigned identity.

    :param tags: A dictionary of strings can be passed as tag metadata to the user assigned identity object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure user assigned identity exists:
            azurerm.managed_service_identity.user_assigned_identity.present:
                - name: test_identity
                - resource_group: test_group
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

    identity = await hub.exec.azurerm.managed_service_identity.user_assigned_identity.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in identity:
        action = "update"

        # tag changes
        tag_changes = differ.deep_diff(identity.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "User assigned identity {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "User assigned identity {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "User assigned identity {0} would be created.".format(name)
        ret["result"] = None
        return ret

    identity_kwargs = kwargs.copy()
    identity_kwargs.update(connection_auth)

    identity = await hub.exec.azurerm.managed_service_identity.user_assigned_identity.create_or_update(
        ctx=ctx, name=name, resource_group=resource_group, tags=tags, **identity_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": identity}

    if "error" not in identity:
        ret["result"] = True
        ret["comment"] = f"User assigned identity {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} user assigned identity {1}! ({2})".format(
        action, name, identity.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Ensure the specified user assigned identity does not exist within the specified resource group.

    :param name: The name of the user assigned identity.

    :param resource_group: The resource group assigned to the user assigned identity.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure user assigned identity absent:
            azurerm.managed_service_identity.user_assigned_identity.absent:
              - name: test_identity
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

    identity = await hub.exec.azurerm.managed_service_identity.user_assigned_identity.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in identity:
        ret["result"] = True
        ret["comment"] = "User assigned identity {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "User assigned identity {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": identity,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.managed_service_identity.user_assigned_identity.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "User assigned identity {0} has been deleted.".format(name)
        ret["changes"] = {"old": identity, "new": {}}
        return ret

    ret["comment"] = "Failed to delete user assigned identity {0}!".format(name)
    return ret
