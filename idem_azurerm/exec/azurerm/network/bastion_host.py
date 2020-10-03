# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Bastion Host Execution Module

.. versionadded:: 4.0.0

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
    hub, ctx, name, resource_group, ip_configuration, dns_name=None, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Creates or updates the specified Bastion Host.

    :param name: The name of the Bastion Host.

    :param resource_group: The resource group of the Bastion Host.

    :param ip_configuration: A dictionary representing a valid BastionHostIPConfiguration object. Valid parameters
        include the following:

        - ``name``: (Required) The name of the BastionHostIPConfiguration resource that is unique within the resource
          group.
        - ``public_ip_address``: (Required) The resource ID of the public IP address which will be assigned to the
          Bastion Host object. The public ip address must have a "Standard" sku.
        - ``subnet``: (Required) The resource ID of the "AzureBastionSubnet" subnet which will be used by the Bastion
          Host.
        - ``private_ip_allocation_method``: (Optional) The Private IP allocation method. Possible values are: 'Static'
          and 'Dynamic'.

    :param dns_name: FQDN for the endpoint on which bastion host is accessible.

    CLI Example:

    .. code-block:: bash

        azurerm.network.bastion_host.create_or_update test_name test_group test_configs

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

    try:
        if not isinstance(ip_configuration["public_ip_address"], dict):
            ip_configuration["public_ip_address"] = {
                "id": ip_configuration["public_ip_address"]
            }
    except KeyError as exc:
        log.error(
            "The resource ID of a public IP address must be declared within the ``ip_configration`` parameter."
        )
        result = {
            "error": "The resource ID of a public IP address must be declared within the ``ip_configration`` parameter."
        }
        return result

    try:
        if not isinstance(ip_configuration["subnet"], dict):
            ip_configuration["subnet"] = {"id": ip_configuration["subnet"]}
    except KeyError as exc:
        log.error(
            "The resource ID of the AzureBastionSubnet subnet must be declared within the ``ip_configration`` parameter."
        )
        result = {
            "error": "The resource ID of a AzureBastionSubnet subnet must be declared within the ``ip_configration`` parameter."
        }
        return result

    try:
        host_model = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "BastionHost",
            ip_configurations=[ip_configuration],
            dns_name=dns_name,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        host = netconn.bastion_hosts.create_or_update(
            resource_group_name=resource_group,
            bastion_host_name=name,
            parameters=host_model,
        )

        host.wait()
        result = host.result().as_dict()
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
    .. versionadded:: 4.0.0

    Deletes the specified Bastion Host.

    :param name: The name of the Bastion Host to delete.

    :param resource_group: The resource group of the Bastion Host.

    CLI Example:

    .. code-block:: bash

        azurerm.network.bastion_host.delete test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        host = netconn.bastion_hosts.delete(
            bastion_host_name=name, resource_group_name=resource_group
        )

        host.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets the specified Bastion Host within the specified resource group.

    :param name: The name of the Bastion Host to query.

    :param resource_group: The resource group of the Bastion Host.

    CLI Example:

    .. code-block:: bash

        azurerm.network.bastion_host.get test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        host = netconn.bastion_hosts.get(
            bastion_host_name=name, resource_group_name=resource_group,
        )

        result = host.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Lists all Bastion Hosts in a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.bastion_host.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        if resource_group:
            hosts = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.bastion_hosts.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            hosts = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.bastion_hosts.list()
            )

        for host in hosts:
            result[host["name"]] = host
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
