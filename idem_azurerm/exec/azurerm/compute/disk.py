# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Disk Execution Module

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
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets information about a disk.

    :param name: The disk to query.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.disk.get test_name test_group

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        disk = compconn.disks.get(resource_group_name=resource_group, disk_name=name)
        result = disk.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a disk.

    :param name: The disk to delete.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.disk.delete test_name test_group

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        disk = compconn.disks.delete(resource_group_name=resource_group, disk_name=name)
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Lists all the disks under a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.disk.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        if resource_group:
            disks = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.disks.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            disks = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.disks.list()
            )

        for disk in disks:
            result[disk["name"]] = disk
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def grant_access(hub, ctx, name, resource_group, access, duration, **kwargs):
    """
    .. versionadded:: 4.0.0

    Grants access to a disk.

    :param name: The name of the disk to grant access to.

    :param resource_group: The resource group name assigned to the disk.

    :param access: Possible values include: 'None', 'Read', 'Write'.

    :param duration: Time duration in seconds until the SAS access expires.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.disk.grant_access test_name test_group

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        disk = compconn.disks.grant_access(
            resource_group_name=resource_group,
            disk_name=name,
            access=access,
            duration_in_seconds=duration,
        )
        disk.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def revoke_access(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Revokes access to a disk.

    :param name: The name of the disk to revoke access to.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.disk.revoke_access test_name test_group

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        disk = compconn.disks.revoke_access(
            resource_group_name=resource_group, disk_name=name
        )
        disk.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
