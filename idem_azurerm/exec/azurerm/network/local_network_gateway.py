# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Local Network Gateway Execution Module

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


async def create_or_update(hub, name, resource_group, gateway_ip_address, **kwargs):
    """
    .. versionadded:: 1.0.0

    Creates or updates a local network gateway object in the specified resource group.

    :param name: The name of the local network gateway object to be created or updated.

    :param resource_group: The name of the resource group associated with the local network gateway.

    :param gateway_ip_address: IP address of the local network gateway.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.create_or_update test_name test_group test_ip

    """
    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(resource_group, **kwargs)

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return False
        kwargs["location"] = rg_props["location"]

    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)

    try:
        gatewaymodel = await hub.exec.utils.azurerm.create_object_model(
            "network",
            "LocalNetworkGateway",
            gateway_ip_address=gateway_ip_address,
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
        gateway_result = gateway.result()
        result = gateway_result.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def get(hub, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the details of a specific local network gateway within a specified resource group.

    :param name: The name of the local network gateway.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.get test_name test_group

    """
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        gateway = netconn.local_network_gateways.get(
            resource_group_name=resource_group, local_network_gateway_name=name
        )

        result = gateway.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, name, resource_group, **kwargs):
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
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        gateway = netconn.local_network_gateways.delete(
            resource_group_name=resource_group, local_network_gateway_name=name
        )
        gateway.wait()
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)

    return result


async def list_(hub, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Lists all local network gateways within a resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.network.local_network_gateway.list test_group

    """
    result = {}
    netconn = await hub.exec.utils.azurerm.get_client("network", **kwargs)
    try:
        gateways = await hub.exec.utils.azurerm.paged_object_to_list(
            netconn.local_network_gateways.list(resource_group_name=resource_group)
        )

        for gateway in gateways:
            result[gateway["name"]] = gateway
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
