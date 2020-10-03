# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Compute Proximity Placement Group Execution Module

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
    hub, ctx, name, resource_group, group_type="standard", **kwargs
):
    """
    .. versionadded:: 4.0.0

    Create or update a proximity placement group.

    :param name: The name of the proximity placement group.

    :param resource_group: The name of the resource group.

    :param group_type: The type of the proximity placement group. Possible values include: "standard", "ultra".
        Defaults to "standard".

    CLI Example:

    .. code-block:: bash

        azurerm.compute.proximity_placement_group.create_or_update test_name test_rg test_type

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

    try:
        groupmodel = await hub.exec.azurerm.utils.create_object_model(
            "compute",
            "ProximityPlacementGroup",
            proximity_placement_group_type=group_type,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        ppg = compconn.proximity_placement_groups.create_or_update(
            resource_group_name=resource_group,
            proximity_placement_group_name=name,
            parameters=groupmodel,
        )

        result = ppg.as_dict()
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

    Delete a proximity placement group.

    :param name: The name of the proximity placement group to delete.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.proximity_placement_group.delete test_name test_rg

    """
    result = False
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        ppg = compconn.proximity_placement_groups.delete(
            resource_group_name=resource_group, proximity_placement_group_name=name
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Retrieves information about a proximity placement group.

    :param name: The proximity placement group to query.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.proximity_placement_group.get test_name test_rg

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        ppg = compconn.proximity_placement_groups.get(
            resource_group_name=resource_group, proximity_placement_group_name=name
        )

        result = ppg.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Lists all proximity placement groups in a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.compute.proximity_placement_group.list

    """
    result = {}
    compconn = await hub.exec.azurerm.utils.get_client(ctx, "compute", **kwargs)

    try:
        if resource_group:
            ppgs = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.proximity_placement_groups.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            ppgs = await hub.exec.azurerm.utils.paged_object_to_list(
                compconn.proximity_placement_groups.list_by_subscription()
            )

        for ppg in ppgs:
            result[ppg["name"]] = ppg
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
