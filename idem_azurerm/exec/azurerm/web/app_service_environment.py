# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Web App Service Environment Operations Execution Module

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
    from azure.mgmt.web.v2019_08_01.models._models_py3 import (
        DefaultErrorResponseException,
    )
    from msrestazure.tools import is_valid_resource_id, parse_resource_id

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, resource_group, virtual_network, subnet, **kwargs,
):
    """
    .. versionadded:: VERSION

    Creates or updates an App Service Plan.

    :param name: The name of the App Service Plan.

    :param resource_group: The name of the resource group.

    :param virtual_network: The resource ID of the virtual network for the App Service Environment.

    :param subnet: The name of the subnet used for the App Service Environment.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_environment.create_or_update test_name test_group test_vnet test_subnet

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

    if not is_valid_resource_id(virtual_network):
        result = {"error": "The given virtual network resource ID is invalid."}
        return result

    vnet_profile = {"id": virtual_network, "subnet": subnet}

    try:
        environmentmodel = await hub.exec.azurerm.utils.create_object_model(
            "web",
            "AppServiceEnvironmentResource",
            app_service_environment_resource_name=name,
            app_service_environment_resource_location=kwargs["location"],
            virtual_network=vnet_profile,
            worker_pools=[],
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        environment = webconn.app_service_environments.create_or_update(
            name=name,
            resource_group_name=resource_group,
            hosting_environment_envelope=environmentmodel,
        )

        environment.wait()
        result = environment.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (ValidationError, DefaultErrorResponseException) as exc:
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, force_delete=None, **kwargs):
    """
    .. versionadded:: VERSION

    Delete an App Service Environment.

    :param name: The name of the App Service Environment.

    :param resource_group: The name of the resource group.

    :param force_delete: Specify true to force the deletion even if the App Service Environment contains resources.
        The default is false.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_environment.delete test_name test_group

    """
    result = False
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        environment = webconn.app_service_environments.delete(
            name=name, resource_group_name=resource_group, force_delete=force_delete
        )

        environment.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Get the properties of an App Service Environment.

    :param name: The name of the App Service Environment.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_environment.get test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        environment = webconn.app_service_environments.get(
            name=name, resource_group_name=resource_group,
        )

        result = environment.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: VERSION

    Get all App Service Environments for a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_environment.list

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        environments = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.app_service_environments.list()
        )

        for environment in environments:
            result[environment["name"]] = environment
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_app_service_plans(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Get all App Service Plans in an App Service Environment.

    :param name: The name of the App Service Environment.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_environment.list_app_service_plans test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        plans = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.app_service_environments.list_app_service_plans(
                name=name, resource_group_name=resource_group
            )
        )

        for plan in plans:
            result[plan["name"]] = plan
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_resource_group(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Get all App Service Environments in a resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app_service_environment.list_by_resource_group test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        plans = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.app_service_environments.list_by_resource_group(
                resource_group_name=resource_group
            )
        )

        for environment in environments:
            result[environment["name"]] = environment
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
