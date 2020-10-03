# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Local Network Gateway Execution Module

.. versionadded:: 1.0.0

.. versionchanged:: 4.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function or via acct in order to work properly.

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


async def create_or_update(
    hub,
    ctx,
    name,
    resource_group,
    gateway_ip_address,
    bgp_settings=None,
    address_prefixes=None,
    fqdn=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Creates or updates a local network gateway object in the specified resource group.

    :param name: The name of the local network gateway object to be created or updated.

    :param resource_group: The name of the resource group associated with the local network gateway.

    :param gateway_ip_address: IP address of the local network gateway.

    :param bgp_settings: A dictionary representing a valid BgpSettings object, which stores the local network
        gateway's BGP speaker settings. Valid parameters include:

        - ``asn``: (Required) The BGP speaker's Autonomous System Number. This is an integer value.
        - ``bgp_peering_address``: (Required) The BGP peering address and BGP identifier of this BGP speaker.
          This is a string value.
        - ``peer_weight``: (Optional) The weight added to routes learned from this BGP speaker. This is an
          Integer value.

    :param address_prefixes: (Optional) A list of address blocks reserved for this virtual network in CIDR notation.
        Serves as the local network gateway's site address space.

    :param fqdn: The FQDN of local network gateway.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.create_or_update test_name test_group test_ip

    """
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

    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    if isinstance(address_prefixes, list):
        address_prefixes = {"address_prefixes": address_prefixes}

    try:
        gatewaymodel = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "LocalNetworkGateway",
            gateway_ip_address=gateway_ip_address,
            local_network_address_space=address_prefixes,
            fqdn=fqdn,
            bgp_settings=bgp_settings,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        gateway = netconn.local_network_gateways.create_or_update(
            local_network_gateway_name=name,
            resource_group_name=resource_group,
            parameters=gatewaymodel,
        )

        gateway.wait()
        result = gateway.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the details of a specific local network gateway within a specified resource group.

    :param name: The name of the local network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.get test_name test_group

    """
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        gateway = netconn.local_network_gateways.get(
            resource_group_name=resource_group, local_network_gateway_name=name
        )

        result = gateway.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes the specified local network gateway.

    :param name: The name of the local network gateway that will be deleted.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.delete test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        gateway = netconn.local_network_gateways.delete(
            resource_group_name=resource_group, local_network_gateway_name=name
        )
        gateway.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def list_(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists all local network gateways within a resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.list test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        gateways = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.local_network_gateways.list(resource_group_name=resource_group)
        )

        for gateway in gateways:
            result[gateway["name"]] = gateway
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update_tags(
    hub, ctx, name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Updates local network gateway tags with specified values.

    :param name: The name of the local network gateway.

    :param resource_group: The name of the resource group to which the local network gateway belongs.

    :param tags: The tags of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.update_tags test_name test_group tags='{"owner": "me"}'

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        gateway = netconn.local_network_gateways.update_tags(
            local_network_gateway_name=name,
            resource_group_name=resource_group,
            tags=tags,
        )

        result = gateway.as_dict()
    except (CloudError, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
