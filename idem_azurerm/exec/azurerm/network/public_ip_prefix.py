# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Public IP Prefix Execution Module

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
    hub,
    ctx,
    name,
    resource_group,
    prefix_length,
    sku="standard",
    public_ip_address_version="IPv4",
    zones=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Creates or updates a static or dynamic public IP prefix.

    :param name: The name of the public IP prefix.

    :param resource_group: The resource group of the public IP prefix.

    :param prefix_length: An integer representing the length of the Public IP Prefix. This value is immutable
        once set. If the value of the ``public_ip_address_version`` parameter is "IPv4", then possible values include
        28, 29, 30, 31. If the value of the ``public_ip_address_version`` parameter is "IPv6", then possible values
        include 124, 125, 126, 127.

    :param sku: The name of a public IP prefix SKU. Possible values include: "standard". Defaults to "standard".

    :param public_ip_address_version: The public IP address version. Possible values include: "IPv4" and "IPv6".
        Defaults to "IPv4".

    :param zones: A list of availability zones that denotes where the IP allocated for the resource needs
        to come from.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_prefix.create_or_update test_name test_group test_length

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

    if sku:
        sku = {"name": sku.lower()}

    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        prefix_model = await hub.exec.azurerm.utils.create_object_model(
            "network",
            "PublicIPPrefix",
            prefix_length=prefix_length,
            sku=sku,
            public_ip_address_version=public_ip_address_version,
            zones=zones,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        prefix = netconn.public_ip_prefixes.create_or_update(
            resource_group_name=resource_group,
            public_ip_prefix_name=name,
            parameters=prefix_model,
        )

        prefix.wait()
        result = prefix.result().as_dict()
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

    Deletes the specified public IP prefix.

    :param name: The name of the public IP prefix to delete.

    :param resource_group: The resource group of the public IP prefix.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_prefix.delete test_name test_group

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        prefix = netconn.public_ip_prefixes.delete(
            public_ip_prefix_name=name, resource_group_name=resource_group
        )

        prefix.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, expand=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets the specified public IP prefix in a specified resource group.

    :param name: The name of the public IP prefix to query.

    :param resource_group: The resource group of the public IP prefix.

    :param expand: Expands referenced resources.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_prefix.get test_name test_group

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        prefix = netconn.public_ip_prefixes.get(
            public_ip_prefix_name=name,
            resource_group_name=resource_group,
            expand=expand,
        )

        result = prefix.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets all the public IP prefixes in a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_prefix.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        if resource_group:
            prefixes = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.public_ip_prefixes.list(resource_group_name=resource_group)
            )
        else:
            prefixes = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.public_ip_prefixes.list_all()
            )

        for prefix in prefixes:
            result[prefix["name"]] = prefix
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update_tags(hub, ctx, name, resource_group, tags=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Updates public IP prefix tags.

    :param name: The name of the public IP prefix.

    :param resource_group: The resource group of the public IP prefix.

    :param tags: The resource tags to update.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_prefix.update_tags test_name test_group test_tags

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        prefix = netconn.public_ip_prefixes.update_tags(
            public_ip_prefix_name=name, resource_group_name=resource_group, tags=tags
        )

        result = prefix.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
