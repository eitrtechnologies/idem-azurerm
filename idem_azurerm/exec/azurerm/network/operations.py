# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Execution Module

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
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def check_dns_name_availability(hub, ctx, name, region, **kwargs):
    """
    .. versionadded:: 1.0.0

    Check whether a domain name in the current zone is available for use.

    :param name: The DNS name to query.

    :param region: The region to query for the DNS name in question.

    CLI Example:

    .. code-block:: bash

         azurerm.network.check_dns_name_availability testdnsname westus

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        check_dns_name = netconn.check_dns_name_availability(
            location=region, domain_name_label=name
        )
        result = check_dns_name.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def check_ip_address_availability(
    hub, ctx, ip_address, virtual_network, resource_group, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Check that a private ip address is available within the specified virtual network.

    :param ip_address: The ip_address to query.

    :param virtual_network: The virtual network to query for the IP address in question.

    :param resource_group: The resource group name assigned to the virtual network.

    CLI Example:

    .. code-block:: bash

         azurerm.network.check_ip_address_availability 10.0.0.4 testnet testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        check_ip = netconn.virtual_networks.check_ip_address_availability(
            resource_group_name=resource_group,
            virtual_network_name=virtual_network,
            ip_address=ip_address,
        )
        result = check_ip.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def usages_list(hub, ctx, location, **kwargs):
    """
    .. versionadded:: 1.0.0

    List subscription network usage for a location.

    :param location: The Azure location to query for network usage.

    CLI Example:

    .. code-block:: bash

         azurerm.network.usages_list westus

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        result = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.usages.list(location)
        )
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
