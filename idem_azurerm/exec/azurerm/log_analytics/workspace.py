# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Log Analytics Workspace Execution Module

.. versionadded:: 2.0.0

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
    location,
    sku=None,
    retention=None,
    workspace_capping=None,
    ingestion_public_network_access=None,
    query_public_network_access=None,
    capacity_reservation_level=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Create or update a workspace.

    :param name: The name of the workspace. The name is case insensitive.

    :param resource_group: The resource group name of the workspace.

    :param location: The resource location.

    :param sku: The name of the SKU. Possible values include: "Free", "Standard", "Premium", "PerNode", "PerGB2018",
        "Standalone", and "CapacityReservation".

    :param retention: The workspace data retention period in days. -1 means Unlimited retention for the Unlimited Sku.
        730 days is the maximum allowed for all other Skus.

    :param workspace_capping: A float representing the daily volume cap in GB for ingestion. -1 means unlimited.

    :param ingestion_public_network_access: The network access type for accessing Log Analytics ingestion. Possible
        values include: "Enabled" and "Disabled". Defaults to "Enabled".

    :param query_public_network_access: The network access type for accessing Log Analytics query. Possible values
        include: "Enabled" and "Disabled". Defaults to "Enabled".

    :param capacity_reservation_level: An integer representing the capacity reservation level for this workspace. This
        parameter is only necessary when "CapacityReservation" is passed as the value of the ``sku`` parameter.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.create_or_update test_name test_group test_location

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    if workspace_capping:
        workspace_capping = {"daily_quota_gb": workspace_capping}

    if sku:
        if sku.lower() == "capacityreservation" and capacity_reservation_level:
            sku = {
                "name": sku,
                "capacity_reservation_level": capacity_reservation_level,
            }
        else:
            sku = {"name": sku}

    try:
        spacemodel = await hub.exec.azurerm.utils.create_object_model(
            "loganalytics",
            "Workspace",
            location=location,
            sku=sku,
            retention=retention,
            workspace_capping=workspace_capping,
            public_network_access_for_ingestion=ingestion_public_network_access,
            public_network_access_for_query=query_public_network_access,
            **kwargs,
        )

    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        workspace = logconn.workspaces.create_or_update(
            workspace_name=name,
            resource_group_name=resource_group,
            parameters=spacemodel,
        )

        workspace.wait()
        result = workspace.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, force=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Deletes a workspace. To recover the workspace, create it again with the same name, in the same subscription,
    resource group and location. The name is kept for 14 days and cannot be used for another workspace. To remove
    the workspace completely and release the name, use the force flag.

    :param name: The name of the workspace.

    :param resource_group: The resource group name of the workspace.

    :param force: An optional boolean flag that specifies whether the workspace should be deleted without the option
        of recovery. A workspace that was deleted with this flag set as True cannot be recovered.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.delete test_name test_group

    """
    result = False
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        workspace = logconn.workspaces.delete(
            workspace_name=name, resource_group_name=resource_group, force=force,
        )

        workspace.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets a workspace instance.

    :param name: The name of the workspace.

    :param resource_group: The resource group name of the workspace.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.get test_name test_group

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        workspace = logconn.workspaces.get(
            workspace_name=name, resource_group_name=resource_group
        )

        result = workspace.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Gets the workspaces in a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.list

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        if resource_group:
            workspaces = await hub.exec.azurerm.utils.paged_object_to_list(
                logconn.workspaces.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            workspaces = await hub.exec.azurerm.utils.paged_object_to_list(
                logconn.workspaces.list()
            )

        for workspace in workspaces:
            result[workspace["name"]] = workspace
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)
        result = {"error": str(exc)}
