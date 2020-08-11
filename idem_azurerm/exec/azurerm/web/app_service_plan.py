# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Web App Service Plan Operations Execution Module

.. versionadded:: 3.0.0

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
    from azure.mgmt.web.v2019_08_01.models._models_py3 import (
        DefaultErrorResponseException,
    )

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, resource_group, kind, sku="F1", reserved=None, tags=None, **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates or updates an App Service Plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    :param kind: The kind of the App Service Plan. Possible values include: "linux", "windows", "functionapp"

    :param sku: The SKU (pricing tier) of the App Service Plan. Defaults to "F1".

    :param reserved: This value should be True if you are using a Linux App Service Plan, False otherwise.
        Defaults to False.

    :param tags: Tags associated with the App Service Plan.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.create_or_update test_name test_group test_kind test_sku

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

    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    if not isinstance(sku, dict):
        sku = {"name": sku}

    try:
        planmodel = await hub.exec.azurerm.utils.create_object_model(
            "web",
            "AppServicePlan",
            sku=sku,
            kind=kind,
            reserved=reserved,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        plan = webconn.app_service_plans.create_or_update(
            name=name, resource_group_name=resource_group, app_service_plan=planmodel,
        )

        plan.wait()
        result = plan.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (ValidationError, DefaultErrorResponseException) as exc:
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Delete an App Service Plan.

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
    .. versionadded:: 3.0.0

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
    except AttributeError as exc:
        result = {
            "error": "The specified App Service Plan does not exist within the given resource group."
        }

    return result


async def get_server_farm_skus(hub, ctx, name, resource_group, **kwargs):
    """
     .. versionadded:: 3.0.0

    Gets all selectable SKUs for a given App Service Plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    CLI Example:
    .. code-block:: bash

        azurerm.web.app_service_plan.get_server_farm_skus test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        skus = webconn.app_service_plans.get_server_farm_skus(
            name=name, resource_group_name=resource_group,
        )

        result = skus
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, detailed=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Get all App Service plans for a subscription.

    :param resource_group: The name of the resource group to limit the results.

    :param detailed: Specify True to return all App Service Plan properties. The default is False, which returns a
        subset of the properties. Retrieval of all properties may increase the API latency. If a resource group is
        specified, then all App Service Plan properties are returned regardless of what this parameter is set to.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.list

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        if resource_group:
            plans = await hub.exec.azurerm.utils.paged_object_to_list(
                webconn.app_service_plans.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            plans = await hub.exec.azurerm.utils.paged_object_to_list(
                webconn.app_service_plans.list(detailed=detailed)
            )

        for plan in plans:
            result[plan["name"]] = plan
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (DefaultErrorResponseException) as exc:
        result = {"error": str(exc)}

    return result


async def list_web_apps(hub, ctx, name, resource_group, skip_token=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Get all apps associated with an App Service plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    :param skip_token: Skip to a web app in the list of webapps associated with app service plan. If specified, the
        resulting list will contain web apps starting from (including) the skipToken. Otherwise, the resulting list
        contains web apps from the start of the list.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_plan.list_web_apps test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        apps = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.app_service_plans.list_web_apps(
                name=name, resource_group_name=resource_group, skip_token=skip_token
            )
        )

        for app in apps:
            result[app["name"]] = app
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (DefaultErrorResponseException) as exc:
        result = {"error": str(exc)}

    return result
