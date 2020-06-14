# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network State Module

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
            "states.azurerm.network.network_security_group.present",
        ]
    },
    "subnet_present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.network.virtual_network.present",
            "states.azurerm.network.network_security_group.present",
        ]
    },
}


async def present(
    hub,
    ctx,
    name,
    address_prefixes,
    resource_group,
    dns_servers=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network exists.

    :param name:
        Name of the virtual network.

    :param resource_group:
        The resource group assigned to the virtual network.

    :param address_prefixes:
        A list of CIDR blocks which can be used by subnets within the virtual network.

    :param dns_servers:
        A list of DNS server addresses.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the virtual network object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual network exists:
            azurerm.network.virtual_network.present:
                - name: vnet1
                - resource_group: group1
                - address_prefixes:
                    - '10.0.0.0/8'
                    - '192.168.0.0/16'
                - dns_servers:
                    - '8.8.8.8'
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

    vnet = await hub.exec.azurerm.network.virtual_network.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in vnet:
        action = "update"
        tag_changes = differ.deep_diff(vnet.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        dns_changes = set(dns_servers or []).symmetric_difference(
            set(vnet.get("dhcp_options", {}).get("dns_servers", []))
        )
        if dns_changes:
            ret["changes"]["dns_servers"] = {
                "old": vnet.get("dhcp_options", {}).get("dns_servers", []),
                "new": dns_servers,
            }

        addr_changes = set(address_prefixes or []).symmetric_difference(
            set(vnet.get("address_space", {}).get("address_prefixes", []))
        )
        if addr_changes:
            ret["changes"]["address_space"] = {
                "address_prefixes": {
                    "old": vnet.get("address_space", {}).get("address_prefixes", []),
                    "new": address_prefixes,
                }
            }

        if kwargs.get("enable_ddos_protection", False) != vnet.get(
            "enable_ddos_protection"
        ):
            ret["changes"]["enable_ddos_protection"] = {
                "old": vnet.get("enable_ddos_protection"),
                "new": kwargs.get("enable_ddos_protection"),
            }

        if kwargs.get("enable_vm_protection", False) != vnet.get(
            "enable_vm_protection"
        ):
            ret["changes"]["enable_vm_protection"] = {
                "old": vnet.get("enable_vm_protection"),
                "new": kwargs.get("enable_vm_protection"),
            }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Virtual network {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Virtual network {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "address_space": {"address_prefixes": address_prefixes},
                "dhcp_options": {"dns_servers": dns_servers},
                "enable_ddos_protection": kwargs.get("enable_ddos_protection", False),
                "enable_vm_protection": kwargs.get("enable_vm_protection", False),
                "tags": tags,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Virtual network {0} would be created.".format(name)
        ret["result"] = None
        return ret

    vnet_kwargs = kwargs.copy()
    vnet_kwargs.update(connection_auth)

    vnet = await hub.exec.azurerm.network.virtual_network.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        address_prefixes=address_prefixes,
        dns_servers=dns_servers,
        tags=tags,
        **vnet_kwargs,
    )

    if "error" not in vnet:
        ret["result"] = True
        ret["comment"] = f"Virtual network {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} virtual network {1}! ({2})".format(
        action, name, vnet.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network does not exist in the resource group.

    :param name:
        Name of the virtual network.

    :param resource_group:
        The resource group assigned to the virtual network.

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

    vnet = await hub.exec.azurerm.network.virtual_network.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in vnet:
        ret["result"] = True
        ret["comment"] = "Virtual network {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Virtual network {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": vnet,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.virtual_network.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Virtual network {0} has been deleted.".format(name)
        ret["changes"] = {"old": vnet, "new": {}}
        return ret

    ret["comment"] = "Failed to delete virtual network {0}!".format(name)
    return ret


async def subnet_present(
    hub,
    ctx,
    name,
    address_prefix,
    virtual_network,
    resource_group,
    security_group=None,
    route_table=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Ensure a subnet exists.

    :param name:
        Name of the subnet.

    :param address_prefix:
        A CIDR block used by the subnet within the virtual network.

    :param virtual_network:
        Name of the existing virtual network to contain the subnet.

    :param resource_group:
        The resource group assigned to the virtual network.

    :param security_group:
        The name of the existing network security group to assign to the subnet.

    :param route_table:
        The name of the existing route table to assign to the subnet.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure subnet exists:
            azurerm.network.virtual_network.subnet_present:
                - name: vnet1_sn1
                - virtual_network: vnet1
                - resource_group: group1
                - address_prefix: '192.168.1.0/24'
                - security_group: nsg1
                - route_table: rt1
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

    snet = await hub.exec.azurerm.network.virtual_network.subnet_get(
        ctx,
        name,
        virtual_network,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in snet:
        action = "update"
        if address_prefix != snet.get("address_prefix"):
            ret["changes"]["address_prefix"] = {
                "old": snet.get("address_prefix"),
                "new": address_prefix,
            }

        nsg_name = None
        if snet.get("network_security_group"):
            nsg_name = snet["network_security_group"]["id"].split("/")[-1]

        if security_group and (security_group != nsg_name):
            ret["changes"]["network_security_group"] = {
                "old": nsg_name,
                "new": security_group,
            }

        rttbl_name = None
        if snet.get("route_table"):
            rttbl_name = snet["route_table"]["id"].split("/")[-1]

        if route_table and (route_table != rttbl_name):
            ret["changes"]["route_table"] = {"old": rttbl_name, "new": route_table}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Subnet {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Subnet {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "address_prefix": address_prefix,
                "network_security_group": security_group,
                "route_table": route_table,
            },
        }

    if ctx["test"]:
        ret["comment"] = "Subnet {0} would be created.".format(name)
        ret["result"] = None
        return ret

    snet_kwargs = kwargs.copy()
    snet_kwargs.update(connection_auth)

    snet = await hub.exec.azurerm.network.virtual_network.subnet_create_or_update(
        ctx=ctx,
        name=name,
        virtual_network=virtual_network,
        resource_group=resource_group,
        address_prefix=address_prefix,
        network_security_group=security_group,
        route_table=route_table,
        **snet_kwargs,
    )

    if "error" not in snet:
        ret["result"] = True
        ret["comment"] = f"Subnet {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} subnet {1}! ({2})".format(
        action, name, snet.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def subnet_absent(
    hub, ctx, name, virtual_network, resource_group, connection_auth=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Ensure a virtual network does not exist in the virtual network.

    :param name:
        Name of the subnet.

    :param virtual_network:
        Name of the existing virtual network containing the subnet.

    :param resource_group:
        The resource group assigned to the virtual network.

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

    snet = await hub.exec.azurerm.network.virtual_network.subnet_get(
        ctx,
        name,
        virtual_network,
        resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in snet:
        ret["result"] = True
        ret["comment"] = "Subnet {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Subnet {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": snet,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.virtual_network.subnet_delete(
        ctx, name, virtual_network, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Subnet {0} has been deleted.".format(name)
        ret["changes"] = {"old": snet, "new": {}}
        return ret

    ret["comment"] = "Failed to delete subnet {0}!".format(name)
    return ret
