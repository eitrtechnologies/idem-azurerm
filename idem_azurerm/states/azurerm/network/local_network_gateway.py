# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Local Network Gateway State Module

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
    "present": {"require": ["states.azurerm.resource.group.present",]},
}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    gateway_ip_address,
    bgp_settings=None,
    address_prefixes=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a location network gateway exists.

    :param name:
        Name of the local network gateway.

    :param resource_group:
        The resource group assigned to the local network gateway.

    :param gateway_ip_address:
        IP address of local network gateway.

    :param bgp_settings:
        A dictionary representing a valid BgpSettings object, which stores the local network gateway's BGP speaker
        settings. Valid parameters include:
          - ``asn``: The BGP speaker's Autonomous System Number. This is an integer value.
          - ``bgp_peering_address``: The BGP peering address and BGP identifier of this BGP speaker.
                                     This is a string value.
          - ``peer_weight``: The weight added to routes learned from this BGP speaker. This is an integer value.

    :param address_prefixes:
        A list of CIDR blocks which can be used by subnets within the virtual network.
        Represents the local network site address space.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the local network gateway object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure local network gateway exists:
            azurerm.network.local_network_gateway.present:
                - name: gateway1
                - resource_group: rg-module-testing
                - gateway_ip_address: 192.168.0.1
                - bgp_settings:
                    asn: 65515
                    bgp_peering_address: 10.2.2.2
                    peer_weight: 0
                - address_prefixes:
                    - '10.0.0.0/8'
                    - '192.168.0.0/16'
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

    gateway = await hub.exec.azurerm.network.local_network_gateway.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in gateway:
        action = "update"
        tag_changes = differ.deep_diff(gateway.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        if gateway_ip_address != gateway.get("gateway_ip_address"):
            ret["changes"]["gateway_ip_address"] = {
                "old": gateway.get("gateway_ip_address"),
                "new": gateway_ip_address,
            }

        if bgp_settings:
            if not isinstance(bgp_settings, dict):
                ret["comment"] = "BGP settings must be provided as a dictionary!"
                return ret

            for key in bgp_settings:
                if bgp_settings[key] != gateway.get("bgp_settings", {}).get(key):
                    ret["changes"]["bgp_settings"] = {
                        "old": gateway.get("bgp_settings"),
                        "new": bgp_settings,
                    }
                    break

        addr_changes = set(address_prefixes or []).symmetric_difference(
            set(
                gateway.get("local_network_address_space", {}).get(
                    "address_prefixes", []
                )
            )
        )
        if addr_changes:
            ret["changes"]["local_network_address_space"] = {
                "address_prefixes": {
                    "old": gateway.get("local_network_address_space", {}).get(
                        "address_prefixes", []
                    ),
                    "new": address_prefixes,
                }
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Local network gateway {0} is already present.".format(
                name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Local network gateway {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "gateway_ip_address": gateway_ip_address,
                "tags": tags,
            },
        }

        if bgp_settings:
            ret["changes"]["new"]["bgp_settings"] = bgp_settings
        if address_prefixes:
            ret["changes"]["new"]["local_network_address_space"] = {
                "address_prefixes": address_prefixes
            }

    if ctx["test"]:
        ret["comment"] = "Local network gateway {0} would be created.".format(name)
        ret["result"] = None
        return ret

    gateway_kwargs = kwargs.copy()
    gateway_kwargs.update(connection_auth)

    gateway = await hub.exec.azurerm.network.local_network_gateway.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        gateway_ip_address=gateway_ip_address,
        local_network_address_space={"address_prefixes": address_prefixes},
        bgp_settings=bgp_settings,
        tags=tags,
        **gateway_kwargs,
    )

    if "error" not in gateway:
        ret["result"] = True
        ret["comment"] = f"Local network gateway {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} local network gateway {1}! ({2})".format(
        action, name, gateway.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a local network gateway object does not exist in the resource_group.

    :param name:
        Name of the local network gateway object.

    :param resource_group:
        The resource group associated with the local network gateway.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure local network gateway absent:
            azurerm.network.local_network_gateway.absent:
                - name: gateway1
                - resource_group: group1
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

    gateway = await hub.exec.azurerm.network.local_network_gateway.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in gateway:
        ret["result"] = True
        ret["comment"] = "Local network gateway object {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Local network gateway object {0} would be deleted.".format(
            name
        )
        ret["result"] = None
        ret["changes"] = {
            "old": gateway,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.local_network_gateway.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Local network gateway object {0} has been deleted.".format(
            name
        )
        ret["changes"] = {"old": gateway, "new": {}}
        return ret

    ret["comment"] = "Failed to delete local network gateway object {0}!".format(name)
    return ret
