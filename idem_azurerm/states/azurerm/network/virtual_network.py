# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network State Module

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
from msrestazure.tools import is_valid_resource_id
from operator import itemgetter
import logging

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
    enable_vm_protection=False,
    enable_ddos_protection=False,
    ddos_protection_plan=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Ensure a virtual network exists.

    :param name:
        Name of the virtual network.

    :param resource_group:
        The resource group assigned to the virtual network.

    :param address_prefixes:
        A list of CIDR blocks which can be used by subnets within the virtual network.

    :param dns_servers:
        A list of DNS server addresses.

    :param enable_vm_protection:
        A boolean value indicating if VM protection is enabled for all the subnets in the virtual network.
        Defaults to False.

    :param enable_ddos_protection:
        A boolean value indicating whether a DDoS protection is enabled for all the protected resources in
        the virtual network. It requires a DDoS protection plan associated with the resource. Default to False.

    :param ddos_protection_plan:
        The resource ID of the DDoS protection plan associated with the virtual network. This parameter is required
        when the ``enable_ddos_protection`` parameter is set to True.

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

    if enable_ddos_protection and not ddos_protection_plan:
        log.error(
            "The resource ID of the DDOS Protection Plan must be specified if DDOS protection is going to be enabled."
        )
        ret[
            "comment"
        ] = "The resource ID of the DDOS Protection Plan must be specified if DDOS protection is going to be enabled."
        return ret

    if ddos_protection_plan:
        if not is_valid_resource_id(ddos_protection_plan):
            log.error(
                "The specified resource ID of the DDOS Protection Plan is invalid."
            )
            ret[
                "comment"
            ] = "The specified resource ID of the DDOS Protection Plan is invalid."
            return ret
        ddos_protection_plan = {"id": ddos_protection_plan}

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

        if enable_ddos_protection is not None:
            if enable_ddos_protection != vnet.get("enable_ddos_protection"):
                ret["changes"]["enable_ddos_protection"] = {
                    "old": vnet.get("enable_ddos_protection"),
                    "new": enable_ddos_protection,
                }

        if ddos_protection_plan:
            if ddos_protection_plan.get("id") != vnet.get(
                "ddos_protection_plan", {}
            ).get("id"):
                ret["changes"]["ddos_protection_plan"] = {
                    "old": vnet.get("ddos_protection_plan"),
                    "new": ddos_protection_plan,
                }

        if enable_vm_protection is not None:
            if enable_vm_protection != vnet.get("enable_vm_protection"):
                ret["changes"]["enable_vm_protection"] = {
                    "old": vnet.get("enable_vm_protection"),
                    "new": enable_vm_protection,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Virtual network {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Virtual network {0} would be updated.".format(name)
            return ret

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
        enable_ddos_protection=enable_ddos_protection,
        enable_vm_protection=enable_vm_protection,
        ddos_protection_plan=ddos_protection_plan,
        tags=tags,
        **vnet_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": vnet}

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

    Example usage:

    .. code-block:: yaml

        Ensure virtual network absent:
            azurerm.network.virtual_network.absent:
              - name: test_vnet
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
    service_endpoints=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

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

    :param service_endpoints:
        A list of service endpoints. More information about service endpoints and valid values can be found
        `here <https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoints-overview>`__.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
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

    # Convert the list of service endpoints into a list of ServiceEndpointPropertiesFormat objects
    if isinstance(service_endpoints, list):
        endpoints = []
        for endpoint in service_endpoints:
            endpoints.append({"service": endpoint})
        service_endpoints = endpoints

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

        # Checks for changes within the service_endpoints parameter
        if service_endpoints is not None:
            if len(service_endpoints) == len(snet.get("service_endpoints", [])):
                old_endpoints = sorted(
                    snet.get("service_endpoints", []), key=itemgetter("service")
                )
                new_endpoints = sorted(service_endpoints, key=itemgetter("service"))

                for index, endpoint in enumerate(old_endpoints):
                    if new_endpoints[index].get("service") != endpoint.get("service"):
                        ret["changes"]["service_endpoints"] = {
                            "old": snet.get("service_endpoints", []),
                            "new": service_endpoints,
                        }
                        break
            else:
                ret["changes"]["service_endpoints"] = {
                    "old": snet.get("service_endpoints", []),
                    "new": service_endpoints,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Subnet {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Subnet {0} would be updated.".format(name)
            return ret

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
        service_endpoints=service_endpoints,
        **snet_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": snet}

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

    Example usage:

    .. code-block:: yaml

        Ensure subnet absent:
            azurerm.network.virtual_network.subnet_absent:
              - name: test_subnet
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
        ctx,
        name=name,
        virtual_network=virtual_network,
        resource_group=resource_group,
        **connection_auth,
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Subnet {0} has been deleted.".format(name)
        ret["changes"] = {"old": snet, "new": {}}
        return ret

    ret["comment"] = "Failed to delete subnet {0}!".format(name)
    return ret
