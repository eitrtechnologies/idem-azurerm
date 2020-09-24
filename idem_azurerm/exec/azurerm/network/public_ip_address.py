# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Public IP Address Execution Module

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


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a public IP address.

    :param name: The name of the public IP address to delete.

    :param resource_group: The resource group name assigned to the public IP address.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.delete test-pub-ip testgroup

    """
    result = False
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        pub_ip = netconn.public_ip_addresses.delete(
            public_ip_address_name=name, resource_group_name=resource_group
        )

        pub_ip.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, expand=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Gets the specified public IP address in a specified resource group.

    :param name: The name of the public IP address to query.

    :param resource_group: The resource group of the public IP address.

    :param expand: Expands referenced resources.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.get test-pub-ip testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        pub_ip = netconn.public_ip_addresses.get(
            public_ip_address_name=name,
            resource_group_name=resource_group,
            expand=expand,
        )

        result = pub_ip.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Creates or updates a static or dynamic public IP address.

    :param name: The name of the public IP address to create.

    :param resource_group: The resource group of the public IP address.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.create_or_update test-ip-0 testgroup

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
        pub_ip_model = await hub.exec.azurerm.utils.create_object_model(
            "network", "PublicIPAddress", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        ip = netconn.public_ip_addresses.create_or_update(
            resource_group_name=resource_group,
            public_ip_address_name=name,
            parameters=pub_ip_model,
        )

        ip.wait()
        result = ip.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Gets all the public IP addresses in a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.list

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        if resource_group:
            pub_ips = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.public_ip_addresses.list(resource_group_name=resource_group)
            )
        else:
            pub_ips = await hub.exec.azurerm.utils.paged_object_to_list(
                netconn.public_ip_addresses.list_all()
            )

        for ip in pub_ips:
            result[ip["name"]] = ip
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update_tags(hub, ctx, name, resource_group, tags=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Updates public IP address tags.

    :param name: The name of the public IP address.

    :param resource_group: The resource group of the public IP address.

    :param tags: The resource tags to update.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.update_tags test_name test_group test_tags

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)

    try:
        pub_ip = netconn.public_ip_addresses.update_tags(
            public_ip_address_name=name, resource_group_name=resource_group, tags=tags
        )

        result = pub_ip.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
