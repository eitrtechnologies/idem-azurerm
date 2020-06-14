# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Route State Module

.. versionadded:: 1.0.0

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

    Example states using Azure Resource Manager authentication:

    .. code-block:: jinja

        Ensure virtual network exists:
            azurerm.network.virtual_network.present:
                - name: my_vnet
                - resource_group: my_rg
                - address_prefixes:
                    - '10.0.0.0/8'
                    - '192.168.0.0/16'
                - dns_servers:
                    - '8.8.8.8'
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure virtual network is absent:
            azurerm.network.virtual_network.absent:
                - name: other_vnet
                - resource_group: my_rg
                - connection_auth: {{ profile }}

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging
import re

log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.route.table_present",
        ]
    },
    "table_present": {"require": ["states.azurerm.resource.group.present",]},
}


async def table_present(
    hub,
    ctx,
    name,
    resource_group,
    tags=None,
    routes=None,
    disable_bgp_route_propagation=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a route table exists.

    :param name:
        Name of the route table.

    :param resource_group:
        The resource group assigned to the route table.

    :param routes:
        An optional list of dictionaries representing valid Route objects contained within a route table. See the
        documentation for the route_present state or route_create_or_update execution module for more information on
        required and optional parameters for routes. The routes are only managed if this parameter is present. When this
        parameter is absent, implemented routes will not be removed, and will merely become unmanaged.

    :param disable_bgp_route_propagation:
        An optional boolean parameter setting whether to disable the routes learned by BGP on the route table.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the route table object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure route table exists:
            azurerm.network.route.table_present:
                - name: rt1
                - resource_group: group1
                - routes:
                  - name: rt1_route1
                    address_prefix: '0.0.0.0/0'
                    next_hop_type: internet
                  - name: rt1_route2
                    address_prefix: '192.168.0.0/16'
                    next_hop_type: vnetlocal
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

    rt_tbl = await hub.exec.azurerm.network.route.table_get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in rt_tbl:
        action = "update"
        # tag changes
        tag_changes = differ.deep_diff(rt_tbl.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # disable_bgp_route_propagation changes
        # pylint: disable=line-too-long
        if disable_bgp_route_propagation and (
            disable_bgp_route_propagation != rt_tbl.get("disable_bgp_route_propagation")
        ):
            ret["changes"]["disable_bgp_route_propagation"] = {
                "old": rt_tbl.get("disable_bgp_route_propagation"),
                "new": disable_bgp_route_propagation,
            }

        # routes changes
        if routes:
            comp_ret = await hub.exec.azurerm.utils.compare_list_of_dicts(
                rt_tbl.get("routes", []), routes
            )

            if comp_ret.get("comment"):
                ret["comment"] = '"routes" {0}'.format(comp_ret["comment"])
                return ret

            if comp_ret.get("changes"):
                ret["changes"]["routes"] = comp_ret["changes"]

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Route table {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Route table {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "tags": tags,
                "routes": routes,
                "disable_bgp_route_propagation": disable_bgp_route_propagation,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Route table {0} would be created.".format(name)
        ret["result"] = None
        return ret

    rt_tbl_kwargs = kwargs.copy()
    rt_tbl_kwargs.update(connection_auth)

    rt_tbl = await hub.exec.azurerm.network.route.table_create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        disable_bgp_route_propagation=disable_bgp_route_propagation,
        routes=routes,
        tags=tags,
        **rt_tbl_kwargs,
    )

    if "error" not in rt_tbl:
        ret["result"] = True
        ret["comment"] = f"Route table {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} route table {1}! ({2})".format(
        action, name, rt_tbl.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def table_absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a route table does not exist in the resource group.

    :param name:
        Name of the route table.

    :param resource_group:
        The resource group assigned to the route table.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

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

    rt_tbl = await hub.exec.azurerm.network.route.table_get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in rt_tbl:
        ret["result"] = True
        ret["comment"] = "Route table {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Route table {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": rt_tbl,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.route.table_delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Route table {0} has been deleted.".format(name)
        ret["changes"] = {"old": rt_tbl, "new": {}}
        return ret

    ret["comment"] = "Failed to delete route table {0}!".format(name)
    return ret


async def present(
    hub,
    ctx,
    name,
    address_prefix,
    next_hop_type,
    route_table,
    resource_group,
    next_hop_ip_address=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a route exists within a route table.

    :param name:
        Name of the route.

    :param address_prefix:
        The destination CIDR to which the route applies.

    :param next_hop_type:
        The type of Azure hop the packet should be sent to. Possible values are: 'VirtualNetworkGateway', 'VnetLocal',
        'Internet', 'VirtualAppliance', and 'None'.

    :param next_hop_ip_address:
        The IP address packets should be forwarded to. Next hop values are only allowed in routes where the next hop
        type is 'VirtualAppliance'.

    :param route_table:
        The name of the existing route table which will contain the route.

    :param resource_group:
        The resource group assigned to the route table.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure route exists:
            azurerm.network.route.present:
                - name: rt1_route2
                - route_table: rt1
                - resource_group: group1
                - address_prefix: '192.168.0.0/16'
                - next_hop_type: vnetlocal
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

    route = await hub.exec.azurerm.network.route.get(
        ctx,
        name,
        route_table,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in route:
        action = "update"
        if address_prefix != route.get("address_prefix"):
            ret["changes"]["address_prefix"] = {
                "old": route.get("address_prefix"),
                "new": address_prefix,
            }

        if next_hop_type.lower() != route.get("next_hop_type", "").lower():
            ret["changes"]["next_hop_type"] = {
                "old": route.get("next_hop_type"),
                "new": next_hop_type,
            }

        if next_hop_type.lower() == "virtualappliance" and next_hop_ip_address != route.get(
            "next_hop_ip_address"
        ):
            ret["changes"]["next_hop_ip_address"] = {
                "old": route.get("next_hop_ip_address"),
                "new": next_hop_ip_address,
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Route {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Route {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "address_prefix": address_prefix,
                "next_hop_type": next_hop_type,
                "next_hop_ip_address": next_hop_ip_address,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Route {0} would be created.".format(name)
        ret["result"] = None
        return ret

    route_kwargs = kwargs.copy()
    route_kwargs.update(connection_auth)

    route = await hub.exec.azurerm.network.route.create_or_update(
        ctx=ctx,
        name=name,
        route_table=route_table,
        resource_group=resource_group,
        address_prefix=address_prefix,
        next_hop_type=next_hop_type,
        next_hop_ip_address=next_hop_ip_address,
        **route_kwargs,
    )

    if "error" not in route:
        ret["result"] = True
        ret["comment"] = f"Route {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} route {1}! ({2})".format(
        action, name, route.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(
    hub, ctx, name, route_table, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Ensure a route table does not exist in the resource group.

    :param name:
        Name of the route table.

    :param route_table:
        The name of the existing route table containing the route.

    :param resource_group:
        The resource group assigned to the route table.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

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

    route = await hub.exec.azurerm.network.route.get(
        ctx,
        name,
        route_table,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in route:
        ret["result"] = True
        ret["comment"] = "Route {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Route {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": route,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.route.delete(
        ctx, name, route_table, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Route {0} has been deleted.".format(name)
        ret["changes"] = {"old": route, "new": {}}
        return ret

    ret["comment"] = "Failed to delete route {0}!".format(name)
    return ret
