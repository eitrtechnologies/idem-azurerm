# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network Execution Module

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

"""
# Python libs
from __future__ import absolute_import
import logging

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def subnets_list(hub, ctx, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all subnets within a virtual network.

    :param virtual_network: The virtual network name to list subnets within.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnets_list testnet testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        subnets = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.subnets.list(
                resource_group_name=resource_group, virtual_network_name=virtual_network
            )
        )

        for subnet in subnets:
            result[subnet["name"]] = subnet
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def subnet_get(hub, ctx, name, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific subnet.

    :param name: The name of the subnet to query.

    :param virtual_network: The virtual network name containing the subnet.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnet_get testsubnet testnet testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        subnet = netconn.subnets.get(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            subnet_name=name,
        )

        result = subnet.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def subnet_create_or_update(
    hub, ctx, name, address_prefix, virtual_network, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Create or update a subnet.

    :param name: The name assigned to the subnet being created or updated.

    :param address_prefix: A valid CIDR block within the virtual network.

    :param virtual_network: The virtual network name containing the subnet.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnet_create_or_update testsubnet '10.0.0.0/24' testnet testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    # Use NSG name to link to the ID of an existing NSG.
    if kwargs.get("network_security_group"):
        nsg = await hub.exec.azurerm.network.network_security_group.get(
            ctx=ctx,
            name=kwargs["network_security_group"],
            resource_group=resource_group,
            **kwargs,
        )
        if "error" not in nsg:
            kwargs["network_security_group"] = {"id": str(nsg["id"])}

    # Use Route Table name to link to the ID of an existing Route Table.
    if kwargs.get("route_table"):
        rt_table = await hub.exec.azurerm.network.route.table_get(
            ctx=ctx, name=kwargs["route_table"], resource_group=resource_group, **kwargs
        )
        if "error" not in rt_table:
            kwargs["route_table"] = {"id": str(rt_table["id"])}

    try:
        snetmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "Subnet",
            address_prefix=address_prefix,
            resource_group=resource_group,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        subnet = netconn.subnets.create_or_update(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            subnet_name=name,
            subnet_parameters=snetmodel,
        )

        subnet.wait()
        result = subnet.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def subnet_delete(hub, ctx, name, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a subnet.

    :param name: The name of the subnet to delete.

    :param virtual_network: The virtual network name containing the subnet.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnet_delete testsubnet testnet testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        subnet = netconn.subnets.delete(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            subnet_name=name,
        )
        subnet.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    List all virtual networks within a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        if resource_group:
            vnets = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.virtual_networks.list(resource_group_name=resource_group)
            )
        else:
            vnets = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.virtual_networks.list_all()
            )

        for vnet in vnets:
            result[vnet["name"]] = vnet
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(hub, ctx, name, address_prefixes, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a virtual network.

    :param name: The name assigned to the virtual network being created or updated.

    :param address_prefixes: A list of CIDR blocks which can be used by subnets within the virtual network.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.create_or_update testnet ['10.0.0.0/16'] testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(
            ctx, resource_group, **kwargs
        )

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return {
                "error": "Unable to determine location from resource group specified."
            }
        kwargs["location"] = rg_props["location"]

    if not isinstance(address_prefixes, list):
        log.error("Address prefixes must be specified as a list!")
        return {"error": "Address prefixes must be specified as a list!"}

    address_space = {"address_prefixes": address_prefixes}
    dhcp_options = {"dns_servers": kwargs.get("dns_servers")}

    try:
        vnetmodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "VirtualNetwork",
            address_space=address_space,
            dhcp_options=dhcp_options,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        vnet = netconn.virtual_networks.create_or_update(
            virtual_network_name=name,
            resource_group_name=resource_group,
            parameters=vnetmodel,
        )

        vnet.wait()
        result = vnet.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a virtual network.

    :param name: The name of the virtual network to delete.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.delete testnet testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        vnet = netconn.virtual_networks.delete(
            virtual_network_name=name, resource_group_name=resource_group
        )

        vnet.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific virtual network.

    :param name: The name of the virtual network to query.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.get testnet testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        vnet = netconn.virtual_networks.get(
            virtual_network_name=name, resource_group_name=resource_group
        )
        result = vnet.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
