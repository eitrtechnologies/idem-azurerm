# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Virtual Network Rule Operations State Module

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

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.postgresql.server.present",
        ]
    }
}


async def present(
    hub,
    ctx,
    name,
    server_name,
    resource_group,
    subnet_id,
    ignore_missing_endpoint=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Ensures that the specified virtual network rule exists within the given PostgreSQL server.

    :param name: The name of the virtual network rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param subnet_id: The ARM Resource ID of the virtual network subnet. The ID will be in the following format:
        '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}/subnets/{subnetName}'

    :param ignore_missing_endpoint: (Optional) A boolean value representing whether the firewall rule is created before
        the virtual network has the vnet service endpoint enabled.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure vnet rule exists:
            azurerm.postgresql.virtual_network_rule.present:
                - name: my_rule
                - server_name: my_server
                - resource_group: my_rg
                - subnet_id: my_id

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

    rule = await hub.exec.azurerm.postgresql.virtual_network_rule.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in rule:
        action = "update"
        if ignore_missing_endpoint is not None:
            if ignore_missing_endpoint != rule.get(
                "ignore_missing_vnet_service_endpoint"
            ):
                ret["changes"]["ignore_missing_vnet_service_endpoint"] = {
                    "old": rule.get("ignore_missing_vnet_service_endpoint"),
                    "new": ignore_missing_endpoint,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Virtual Network Rule {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Virtual Network Rule {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Virtual Network Rule {0} would be created.".format(name)
        ret["result"] = None
        return ret

    rule_kwargs = kwargs.copy()
    rule_kwargs.update(connection_auth)

    rule = await hub.exec.azurerm.postgresql.virtual_network_rule.create_or_update(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        subnet_id=subnet_id,
        ignore_missing_endpoint=ignore_missing_endpoint,
        **rule_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": rule}

    if "error" not in rule:
        ret["result"] = True
        ret["comment"] = f"Virtual Network Rule {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Virtual Network Rule {1}! ({2})".format(
        action, name, rule.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, server_name, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Ensures that the specified virtual network rule does not exist within the given PostgreSQL server.

    :param name: The name of the virtual network rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure vnet rule is absent:
            azurerm.postgresql.virtual_network_rule.absent:
                - name: my_rule
                - server_name: my_server
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

    rule = await hub.exec.azurerm.postgresql.virtual_network_rule.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in rule:
        ret["result"] = True
        ret["comment"] = "Virtual Network Rule {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Virtual Network Rule {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": rule,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.postgresql.virtual_network_rule.delete(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        **connection_auth,
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Virtual Network Rule {0} has been deleted.".format(name)
        ret["changes"] = {"old": rule, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Virtual Network Rule {0}!".format(name)
    return ret
