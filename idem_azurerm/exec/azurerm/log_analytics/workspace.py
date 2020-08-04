# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Log Analytics Workspace Execution Module

.. versionadded:: 2.0.0

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
    customer_id=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Create or update a workspace.

    :param name: The name of the workspace.

    :param resource_group: The resource group name of the workspace.

    :param location: The resource location.

    :param sku: The name of the SKU. Possible values include: 'Free', 'Standard', 'Premium', 'Unlimited', 'PerNode',
        'PerGB2018', 'Standalone'.

    :param retention: The workspace data retention in days. -1 means Unlimited retention for the Unlimited Sku.
        730 days is the maximum allowed for all other Skus.

    :param customer_id: The ID associated with the workspace. Setting this value at creation time allows the workspace
        being created to be linked to an existing workspace.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.create test_name test_group test_location

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    if sku:
        sku = {"name": sku}

    try:
        spacemodel = await hub.exec.azurerm.utils.create_object_model(
            "loganalytics",
            "Workspace",
            location=location,
            sku=sku,
            customer_id=customer_id,
            retention=retention,
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


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes a workspace instance.

    :param name: The name of the workspace.

    :param resource_group: The resource group name of the workspace.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.delete test_name test_group

    """
    result = False
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        workspace = logconn.workspaces.delete(
            workspace_name=name, resource_group_name=resource_group
        )

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


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets the workspaces in a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.list

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        workspaces = await hub.exec.azurerm.utils.paged_object_to_list(
            logconn.workspaces.list()
        )

        for workspace in workspaces:
            result[workspace["name"]] = workspace
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_resource_group(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets the workspaces in a resource group.

    :param resource_group: The name of the resource group to get. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.list_by_resource_group test_group

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        workspaces = await hub.exec.azurerm.utils.paged_object_to_list(
            logconn.workspaces.list_by_resource_group(
                resource_group_name=resource_group
            )
        )

        for workspace in workspaces:
            result[workspace["name"]] = workspace
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_intelligence_packs(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Lists all the intelligence packs possible and whether they are enabled or disabled for a given workspace.

    :param name: Name of the workspace.

    :param resource_group: The resource group name of the workspace.

    CLI Example:

    .. code-block:: bash

        azurerm.log_analytics.workspace.list_intelligence_packs test_name test_group

    """
    result = {}
    logconn = await hub.exec.azurerm.utils.get_client(ctx, "loganalytics", **kwargs)

    try:
        packs = logconn.workspaces.list_intelligence_packs(
            workspace_name=name, resource_group_name=resource_group
        )

        for pack in packs:
            pack = pack.as_dict()
            result[pack["name"]] = pack
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("loganalytics", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
