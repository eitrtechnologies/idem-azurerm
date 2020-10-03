# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Management Group State Module

.. versionadded:: 2.0.0

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
import logging

log = logging.getLogger(__name__)


async def present(
    hub, ctx, name, display_name=None, parent=None, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Ensures that the specified management group is present.

    :param name: The ID of the Management Group. For example, 00000000-0000-0000-0000-000000000000.

    :param display_name: The friendly name of the management group. If no value is passed then this field will be set
        to the name of the management group.

    :param parent: The fully qualified ID for the parent management group. For example,
        /providers/Microsoft.Management/managementGroups/0000000-0000-0000-0000-000000000000.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management group exists:
            azurerm.managementgroup.operations.present:
                - name: my_mgroup

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

    mgroup = await hub.exec.azurerm.managementgroup.operations.get(
        ctx=ctx, name=name, azurerm_log_level="info", **connection_auth
    )

    if "error" not in mgroup:
        action = "update"
        if parent:
            if parent != mgroup.get("parent", {}).get("id"):
                ret["changes"]["parent"] = {
                    "old": mgroup.get("parent", {}).get("id"),
                    "new": parent,
                }

        if display_name:
            if display_name != mgroup.get("display_name"):
                ret["changes"]["display_name"] = {
                    "old": mgroup.get("display_name"),
                    "new": display_name,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Management Group {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Management Group {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Management Group {0} would be created.".format(name)
        ret["result"] = None
        return ret

    mgroup_kwargs = kwargs.copy()
    mgroup_kwargs.update(connection_auth)

    mgroup = await hub.exec.azurerm.managementgroup.operations.create_or_update(
        ctx=ctx, name=name, parent=parent, display_name=display_name, **mgroup_kwargs
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": mgroup}

    if "error" not in mgroup:
        ret["result"] = True
        ret["comment"] = f"Management Group {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Management Group {1}! ({2})".format(
        action, name, mgroup.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a specified management group does not exist.

    :param name: The ID of the Management Group. For example, 00000000-0000-0000-0000-000000000000.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management group absent:
            azurerm.managementgroup.operations.absent:
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

    mgroup = await hub.exec.azurerm.managementgroup.operations.get(
        ctx=ctx, name=name, azurerm_log_level="info", **connection_auth
    )

    if "error" in mgroup:
        ret["result"] = True
        ret["comment"] = "Management Group {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Management Group {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": mgroup,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.managementgroup.operations.delete(
        ctx=ctx, name=name, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Management Group {0} has been deleted.".format(name)
        ret["changes"] = {"old": mgroup, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Management Group {0}!".format(name)
    return ret
