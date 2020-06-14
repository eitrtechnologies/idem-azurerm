# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Log Analytics Workspace State Module

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
    sku=None,
    retention=None,
    customer_id=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a specified log analytics workspace exists.

    :param name: The name of the workspace.

    :param resource_group: The resource group name of the workspace.

    :param location: The resource location.

    :param sku: The name of the SKU. Possible values include: 'Free', 'Standard', 'Premium', 'Unlimited', 'PerNode',
        'PerGB2018', 'Standalone'.

    :param retention: The workspace data retention in days. -1 means Unlimited retention for the Unlimited Sku.
        730 days is the maximum allowed for all other Skus.

    :param customer_id: The ID associated with the workspace. Setting this value at creation time allows the workspace
        being created to be linked to an existing workspace.

    :param tags: A dictionary of strings can be passed as tag metadata to the key vault.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure log analytics workspace exists:
            azurerm.log_analytics.workspace.present:
                - name: my_vault
                - resource_group: my_rg
                - location: my_location
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

    workspace = await hub.exec.azurerm.log_analytics.workspace.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in workspace:
        action = "update"
        if tags:
            tag_changes = differ.deep_diff(workspace.get("tags", {}), tags)
            if tag_changes:
                ret["changes"]["tags"] = tag_changes

        if sku:
            if sku.lower() != workspace.get("sku").get("name").lower():
                ret["changes"]["sku"] = {
                    "old": workspace.get("sku").get("name"),
                    "new": sku,
                }

        if retention is not None:
            if retention != workspace.get("retention_in_days"):
                ret["changes"]["retention_in_days"] = {
                    "old": workspace.get("retention_in_days"),
                    "new": retention,
                }

        if customer_id:
            if customer_id != workspace.get("customer_id"):
                ret["changes"]["customer_id"] = {
                    "old": workspace.get("customer_id"),
                    "new": customer_id,
                }

        if kwargs.get("etag"):
            if kwargs.get("etag") != workspace.get("e_tag"):
                ret["changes"]["e_tag"] = {
                    "old": workspace.get("e_tag"),
                    "new": kwargs.get("etag"),
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Log Analytics Workspace {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Log Analytics Workspace {0} would be updated.".format(
                name
            )
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "location": location,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if sku:
            ret["changes"]["new"]["sku"] = {"name": sku}
        if customer_id:
            ret["changes"]["new"]["customer_id"] = customer_id
        if retention is not None:
            ret["changes"]["new"]["retention_in_days"] = retention
        if kwargs.get("etag"):
            ret["changes"]["new"]["e_tag"] = kwargs.get("etag")

    if ctx["test"]:
        ret["comment"] = "Log Analytics Workspace {0} would be created.".format(name)
        ret["result"] = None
        return ret

    workspace_kwargs = kwargs.copy()
    workspace_kwargs.update(connection_auth)

    workspace = await hub.exec.azurerm.log_analytics.workspace.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        location=location,
        sku=sku,
        retention=retention,
        customer_id=customer_id,
        tags=tags,
        **workspace_kwargs,
    )

    if "error" not in workspace:
        ret["result"] = True
        ret["comment"] = f"Log Analytics Workspace {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Log Analytics Workspace {1}! ({2})".format(
        action, name, workspace.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a specified Log Analytics Workspace does not exist.

    :param name: The name of the workspace.

    :param resource_group: The resource group name of the workspace.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure log analytics workspace is absent:
            azurerm.log_analytics.workspace.absent:
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

    workspace = await hub.exec.azurerm.log_analytics.workspace.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in workspace:
        ret["result"] = True
        ret["comment"] = "Log Analytics Workspace {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Log Analytics Workspace {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": workspace,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.log_analytics.workspace.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Log Analytics Workspace {0} has been deleted.".format(name)
        ret["changes"] = {"old": workspace, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Log Analytics Workspace {0}!".format(name)
    return ret
