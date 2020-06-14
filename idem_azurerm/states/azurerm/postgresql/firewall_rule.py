# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Firewall Rule Operations State Module

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
    start_ip_address,
    end_ip_address,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensures that the specified firewall rule exists within the given PostgreSQL server.

    :param name: The name of the server firewall rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param start_ip_address: The start IP address of the server firewall rule. Must be IPv4 format.

    :param end_ip_address: The end IP address of the server firewall rule. Must be IPv4 format.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure firewall rule exists:
            azurerm.postgresql.firewall_rule.present:
                - name: my_rule
                - server_name: my_server
                - resource_group: my_rg
                - start_ip_address: '0.0.0.0'
                - end_ip_address: '255.255.255.255'
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

    rule = await hub.exec.azurerm.postgresql.firewall_rule.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in rule:
        action = "update"
        if start_ip_address != rule.get("start_ip_address"):
            ret["changes"]["start_ip_address"] = {
                "old": rule.get("start_ip_address"),
                "new": start_ip_address,
            }

        if end_ip_address != rule.get("end_ip_address"):
            ret["changes"]["end_ip_address"] = {
                "old": rule.get("end_ip_address"),
                "new": end_ip_address,
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Firewall Rule {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Firewall Rule {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "server_name": server_name,
                "resource_group": resource_group,
                "start_ip_address": start_ip_address,
                "end_ip_address": end_ip_address,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Firewall Rule {0} would be created.".format(name)
        ret["result"] = None
        return ret

    rule_kwargs = kwargs.copy()
    rule_kwargs.update(connection_auth)

    rule = await hub.exec.azurerm.postgresql.firewall_rule.create_or_update(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        start_ip_address=start_ip_address,
        end_ip_address=end_ip_address,
        **rule_kwargs,
    )

    if "error" not in rule:
        ret["result"] = True
        ret["comment"] = f"Firewall Rule {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Firewall Rule {1}! ({2})".format(
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

    Ensures that the specified firewall rule does not exist within the given PostgreSQL server.

    :param name: The name of the server firewall rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure firewall rule is absent:
            azurerm.postgresql.firewall_rule.absent:
                - name: my_rule
                - server_name: my_server
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

    rule = await hub.exec.azurerm.postgresql.firewall_rule.get(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in rule:
        ret["result"] = True
        ret["comment"] = "Firewall Rule {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Firewall Rule {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": rule,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.postgresql.firewall_rule.delete(
        ctx=ctx,
        name=name,
        server_name=server_name,
        resource_group=resource_group,
        **connection_auth,
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Firewall Rule {0} has been deleted.".format(name)
        ret["changes"] = {"old": rule, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Firewall Rule {0}!".format(name)
    return ret
