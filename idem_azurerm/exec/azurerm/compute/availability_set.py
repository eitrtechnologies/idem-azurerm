# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Availability Set Execution Module

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


async def create_or_update(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Create or update an availability set.

    :param name: The availability set to create.

    :param resource_group: The resource group name assigned to the availability set.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.availability_set.create_or_update testset testgroup

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

    # Use VM names to link to the IDs of existing VMs.
    if isinstance(kwargs.get("virtual_machines"), list):
        vm_list = []
        for vm_name in kwargs.get("virtual_machines"):
            vm_instance = await hub.exec.azurerm.compute.virtual_machine.get(
                ctx=ctx, name=vm_name, resource_group=resource_group, **kwargs
            )
            if "error" not in vm_instance:
                vm_list.append({"id": str(vm_instance["id"])})
        kwargs["virtual_machines"] = vm_list

    try:
        setmodel = await hub.exec.azurerm.utils.create_object_model(
            "compute", "AvailabilitySet", **kwargs
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        av_set = compconn.availability_sets.create_or_update(
            resource_group_name=resource_group,
            availability_set_name=name,
            parameters=setmodel,
        )
        result = av_set.as_dict()

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
    .. versionadded:: 1.0.0

    Delete an availability set.

    :param name: The availability set to delete.

    :param resource_group: The resource group name assigned to the availability set.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.availability_set.delete testset testgroup

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        compconn.availability_sets.delete(
            resource_group_name=resource_group, availability_set_name=name
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get a dictionary representing an availability set's properties.

    :param name: The availability set to get.

    :param resource_group: The resource group name assigned to the availability set.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.availability_set.get testset testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        av_set = compconn.availability_sets.get(
            resource_group_name=resource_group, availability_set_name=name
        )
        result = av_set.as_dict()

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Lists all availability sets in a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.availability_set.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        if resource_group:
            avail_sets = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.availability_sets.list(resource_group_name=resource_group)
            )
        else:
            avail_sets = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.availability_sets.list_by_subscription()
            )

        for avail_set in avail_sets:
            result[avail_set["name"]] = avail_set
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_available_sizes(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    List all available virtual machine sizes that can be used to create a new virtual machine in an existing
    availability set.

    :param name: The availability set name to list available virtual machine sizes within.

    :param resource_group: The resource group name to list available availability set sizes within.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.availability_set.list_available_sizes testset testgroup

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        sizes = await hub.exec.azurerm.utils.paged_object_to_list(
            compconn.availability_sets.list_available_sizes(
                resource_group_name=resource_group, availability_set_name=name
            )
        )

        for size in sizes:
            result[size["name"]] = size
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
