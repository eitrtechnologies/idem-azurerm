# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Web App Service Plan Operations Execution Module

.. versionadded:: VERSION

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
import datetime

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.web.models  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import ValidationError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, resource_group, location, sku, **kwargs,
):
    """
    .. versionadded:: VERSION

    Creates or updates an App Service Plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    :param location: The location the resource.

    :param sku: A dictionary representing the sku (pricing tier) of the app service plan. Possible properties include:
        - ``name``: Name of the resource SKU.
        - ``tier``: Service tier of the resource SKU.
        - ``size``: Size specifier of the resource SKU.
        - ``family``: Family code of the resource SKU.
        - ``capacity``: Current number of instances assigned to the resource. 

{"name": "F1", "tier": "Free", "size": "F1", "family": "F", "capacity": 1}

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.create_or_update test_name test_group test_location

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        planmodel = await hub.exec.azurerm.utils.create_object_model(
            "web",
            "AppServicePlan",
            app_service_plan_name=name,
            location=location,
            sku=sku,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        plan = webconn.app_service_plans.create_or_update(
            name=name, resource_group_name=resource_group, app_service_plan=planmodel
        )

        result = plan.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except ValidationError as exc:
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Delete an App Service plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.delete test_name test_group

    """
    result = False
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        plan = webconn.app_service_plans.delete(
            name=name, resource_group_name=resource_group,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Get an App Service plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.get test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        plan = webconn.app_service_plans.get(
            name=name, resource_group_name=resource_group,
        )

        result = plan.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, detailed=None, **kwargs):
    """
    .. versionadded:: VERSION

    Get all App Service plans for a subscription.

    :param detailed: Specify true to return all App Service plan properties. The default is false, which returns a
        subset of the properties. Retrieval of all properties may increase the API latency.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.list

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        plans = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.app_service_plans.list(detailed=detailed)
        )

        for plan in plans:
            result[plan["name"]] = plan
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
