# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Network Public IP Address Execution Module

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


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a public IP address.

    :param name: The name of the public IP address to delete.

    :param resource_group: The resource group name assigned to the
        public IP address.

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


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get details about a specific public IP address.

    :param name: The name of the public IP address to query.

    :param resource_group: The resource group name assigned to the
        public IP address.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.get test-pub-ip testgroup

    """
    expand = kwargs.get("expand")

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

    Create or update a public IP address within a specified resource group.

    :param name: The name of the public IP address to create.

    :param resource_group: The resource group name assigned to the
        public IP address.

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
        ip_result = ip.result()
        result = ip_result.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def list_all(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all public IP addresses within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.list_all

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        pub_ips = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.public_ip_addresses.list_all()
        )

        for ip in pub_ips:
            result[ip["name"]] = ip
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all public IP addresses within a resource group.

    :param resource_group: The resource group name to list public IP
        addresses within.

    CLI Example:

    .. code-block:: bash

        azurerm.network.public_ip_address.list testgroup

    """
    result = {}
    netconn = await hub.exec.azurerm.utils.get_client(ctx, "network", **kwargs)
    try:
        pub_ips = await hub.exec.azurerm.utils.paged_object_to_list(
            netconn.public_ip_addresses.list(resource_group_name=resource_group)
        )

        for ip in pub_ips:
            result[ip["name"]] = ip
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("network", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
