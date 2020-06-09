# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) DNS Zone Execution Module

.. versionadded:: 1.0.0

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
    import azure.mgmt.dns.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Creates or updates a DNS zone. Does not modify DNS records within the zone.

    :param name: The name of the DNS zone to create (without a terminating dot).

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.zone.create_or_update myzone testgroup

    """
    # DNS zones are global objects
    kwargs["location"] = "global"

    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)

    # Convert list of ID strings to list of dictionaries with id key.
    if isinstance(kwargs.get("registration_virtual_networks"), list):
        kwargs["registration_virtual_networks"] = [
            {"id": vnet} for vnet in kwargs["registration_virtual_networks"]
        ]

    if isinstance(kwargs.get("resolution_virtual_networks"), list):
        kwargs["resolution_virtual_networks"] = [
            {"id": vnet} for vnet in kwargs["resolution_virtual_networks"]
        ]

    try:
        zone_model = await hub.exec.azurerm.utils.create_object_model(
            "dns", "Zone", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        zone = dnsconn.zones.create_or_update(
            zone_name=name,
            resource_group_name=resource_group,
            parameters=zone_model,
            if_match=kwargs.get("if_match"),
            if_none_match=kwargs.get("if_none_match"),
        )
        result = zone.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a DNS zone within a resource group.

    :param name: The name of the DNS zone to delete.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.zone.delete myzone testgroup

    """
    result = False
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        zone = dnsconn.zones.delete(
            zone_name=name,
            resource_group_name=resource_group,
            if_match=kwargs.get("if_match"),
        )
        zone.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get a dictionary representing a DNS zone's properties, but not the
    record sets within the zone.

    :param name: The DNS zone to get.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.zone.get myzone testgroup

    """
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        zone = dnsconn.zones.get(zone_name=name, resource_group_name=resource_group)
        result = zone.as_dict()

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_resource_group(hub, ctx, resource_group, top=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists the DNS zones in a resource group.

    :param resource_group: The name of the resource group.

    :param top: The maximum number of DNS zones to return. If not specified,
    returns up to 100 zones.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.zone.list_by_resource_group testgroup

    """
    result = {}
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        zones = await hub.exec.azurerm.utils.paged_object_to_list(
            dnsconn.zones.list_by_resource_group(
                resource_group_name=resource_group, top=top
            )
        )

        for zone in zones:
            result[zone["name"]] = zone
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, top=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists the DNS zones in all resource groups in a subscription.

    :param top: The maximum number of DNS zones to return. If not specified,
    returns up to 100 zones.

    CLI Example:

    .. code-block:: bash

        azurerm.dns.zone.list

    """
    result = {}
    dnsconn = await hub.exec.azurerm.utils.get_client(ctx, "dns", **kwargs)
    try:
        zones = await hub.exec.azurerm.utils.paged_object_to_list(
            dnsconn.zones.list(top=top)
        )

        for zone in zones:
            result[zone["name"]] = zone
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
