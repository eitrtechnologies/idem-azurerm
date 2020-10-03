# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Resource Group Execution Module

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
    import azure.mgmt.resource.resources.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all resource groups within a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.group.list

    """
    result = {}
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)
    try:
        groups = await hub.exec.azurerm.utils.paged_object_to_list(
            resconn.resource_groups.list()
        )

        for group in groups:
            result[group["name"]] = group
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def check_existence(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Check for the existence of a named resource group in the current subscription.

    :param name: The resource group name to check.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.group.check_existence testgroup

    """
    result = False
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)
    try:
        result = resconn.resource_groups.check_existence(resource_group_name=name)

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get a dictionary representing a resource group's properties.

    :param name: The resource group name to get.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.group.get testgroup

    """
    result = {}
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)
    try:
        group = resconn.resource_groups.get(resource_group_name=name)

        result = group.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update(hub, ctx, name, location, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update a resource group in a given location.

    :param name: The name of the resource group to create or update.

    :param location: The location of the resource group. This value is not able to be updated once the resource
        group is created.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.group.create_or_update testgroup "westus"

    """
    result = {}
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)
    resource_group_params = {
        "location": location,
        "managed_by": kwargs.get("managed_by"),
        "tags": kwargs.get("tags"),
    }
    try:
        group = resconn.resource_groups.create_or_update(name, resource_group_params)

        result = group.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a resource group from the subscription.

    :param name: The resource group name to delete.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.group.delete testgroup

    """
    result = False
    resconn = await hub.exec.azurerm.utils.get_client(ctx, "resource", **kwargs)
    try:
        group = resconn.resource_groups.delete(resource_group_name=name)

        group.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)

    return result
