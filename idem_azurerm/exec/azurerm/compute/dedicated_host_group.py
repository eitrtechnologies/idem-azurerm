# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Dedicated Host Group Execution Module

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
    import azure.mgmt.compute.models  # pylint: disable=unused-import
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
    platform_fault_domain_count,
    zone=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Create or update a dedicated host group. More information about Dedicated Host Groups can be found
    `here <https://go.microsoft.com/fwlink/?linkid=2082596/>`__.

    :param name: The name of the dedicated host group.

    :param resource_group: The name of the resource group name assigned to the dedicated host group.

    :param platform_fault_domain_count: The number of fault domains that the host group can span.

    :param zone: The Availability Zone to use for this host group. The zone can only be assigned during creation. If
        not provided, the group supports all zones in the region. If provided, enforces each host in the group to be
        in the same zone.

    :param tags: A dictionary of strings can be passed as tag metadata to the dedicate host group resource object.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.dedicated_host_group.create_or_update test_name test_group

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
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    if zone and not isinstance(zone, list):
        zone = [zone]

    try:
        groupmodel = await hub.exec.azurerm.utils.create_object_model(
            "compute",
            "DedicatedHostGroup",
            platform_fault_domain_count=platform_fault_domain_count,
            zones=zone,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        host_group = compconn.dedicated_host_groups.create_or_update(
            resource_group_name=resource_group,
            host_group_name=name,
            parameters=groupmodel,
        )

        result = host_group.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Delete a dedicated host group.

    :param name: The dedicated host group to delete.

    :param resource_group: The resource group name assigned to the dedicated host group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.dedicated_host_group.delete test_name test_group

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        key = compconn.dedicated_host_groups.delete(
            resource_group_name=resource_group, host_group_name=name
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Retrieves information about a dedicated host group.

    :param name: The name of the dedicated host group to get.

    :param resource_group: The resource group name assigned to the dedicated host group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.dedicated_host_group.get test_name test_group

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        host_group = compconn.dedicated_host_groups.get(
            resource_group_name=resource_group, host_group_name=name
        )

        result = host_group.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Lists all of the dedicated host gorups in the subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.dedicated_host_group.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        if resource_group:
            host_groups = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.dedicated_host_groups.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            host_groups = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.dedicated_host_groups.list_by_subscription()
            )

        for group in host_groups:
            result[group["name"]] = group
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
