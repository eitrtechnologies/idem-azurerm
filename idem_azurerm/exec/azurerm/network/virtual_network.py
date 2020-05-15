# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Virtual Network Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.36.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.1
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function in order to work properly.

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

try:
    from six.moves import range as six_range
except ImportError:
    six_range = range

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def subnets_list(hub, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all subnets within a virtual network.

    :param virtual_network: The virtual network name to list subnets within.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnets_list testnet testgroup

    """
    result = {}
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        subnets = await hub.exec.utils.azurerm.paged_object_to_list(
            netconn.subnets.list(
                resource_group_name=resource_group, virtual_network_name=virtual_network
            )
        )

        for subnet in subnets:
            result[subnet["name"]] = subnet
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def subnet_get(hub, name, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific subnet.

    :param name: The name of the subnet to query.

    :param virtual_network: The virtual network name containing the
        subnet.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnet_get testsubnet testnet testgroup

    """
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        subnet = netconn.subnets.get(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            subnet_name=name,
        )

        result = subnet.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def subnet_create_or_update(
    hub, name, address_prefix, virtual_network, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Create or update a subnet.

    :param name: The name assigned to the subnet being created or updated.

    :param address_prefix: A valid CIDR block within the virtual network.

    :param virtual_network: The virtual network name containing the
        subnet.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnet_create_or_update testsubnet \
                  '10.0.0.0/24' testnet testgroup

    """
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)

    # Use NSG name to link to the ID of an existing NSG.
    if kwargs.get("network_security_group"):
        nsg = network_security_group_get(
            name=kwargs["network_security_group"],
            resource_group=resource_group,
            **kwargs,
        )
        if "error" not in nsg:
            kwargs["network_security_group"] = {"id": str(nsg["id"])}

    # Use Route Table name to link to the ID of an existing Route Table.
    if kwargs.get("route_table"):
        rt_table = route_table_get(
            name=kwargs["route_table"], resource_group=resource_group, **kwargs
        )
        if "error" not in rt_table:
            kwargs["route_table"] = {"id": str(rt_table["id"])}

    try:
        snetmodel = await hub.exec.utils.azurerm.create_object_model(
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
        sn_result = subnet.result()
        result = sn_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def subnet_delete(hub, name, virtual_network, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a subnet.

    :param name: The name of the subnet to delete.

    :param virtual_network: The virtual network name containing the
        subnet.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network_gateway.subnet_delete testsubnet testnet testgroup

    """
    result = False
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        subnet = netconn.subnets.delete(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            subnet_name=name,
        )
        subnet.wait()
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)

    return result


async def list_all(hub, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all virtual networks within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.list_all

    """
    result = {}
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        vnets = await hub.exec.utils.azurerm.paged_object_to_list(
            netconn.virtual_networks.list_all()
        )

        for vnet in vnets:
            result[vnet["name"]] = vnet
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all virtual networks within a resource group.

    :param resource_group: The resource group name to list virtual networks
        within.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.list testgroup

    """
    result = {}
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        vnets = await hub.exec.utils.azurerm.paged_object_to_list(
            netconn.virtual_networks.list(resource_group_name=resource_group)
        )

        for vnet in vnets:
            result[vnet["name"]] = vnet
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(hub, name, address_prefixes, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a virtual network.

    :param name: The name assigned to the virtual network being
        created or updated.

    :param address_prefixes: A list of CIDR blocks which can be used
        by subnets within the virtual network.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.create_or_update \
                  testnet ['10.0.0.0/16'] testgroup

    """
    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(resource_group, **kwargs)

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return False
        kwargs["location"] = rg_props["location"]

    if not isinstance(address_prefixes, list):
        log.error("Address prefixes must be specified as a list!")
        return False

    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)

    address_space = {"address_prefixes": address_prefixes}
    dhcp_options = {"dns_servers": kwargs.get("dns_servers")}

    try:
        vnetmodel = await hub.exec.utils.azurerm.create_object_model(
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
        vnet_result = vnet.result()
        result = vnet_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a virtual network.

    :param name: The name of the virtual network to delete.

    :param resource_group: The resource group name assigned to the
        virtual network

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.delete testnet testgroup

    """
    result = False
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        vnet = netconn.virtual_networks.delete(
            virtual_network_name=name, resource_group_name=resource_group
        )
        vnet.wait()
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific virtual network.

    :param name: The name of the virtual network to query.

    :param resource_group: The resource group name assigned to the
        virtual network.

    CLI Example:

    .. code-block:: bash

        azurerm.network.virtual_network.get testnet testgroup

    """
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        vnet = netconn.virtual_networks.get(
            virtual_network_name=name, resource_group_name=resource_group
        )
        result = vnet.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
