# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Web App Operations Execution Module

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

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, resource_group, kind=None, server_farm_id=None, **kwargs
):
    """
    .. versionadded:: VERSION

    Create function for web site, or a deployment slot.

    :param name: Unique name of the app to create or update.

    :param resource_group: The name of the resource group.

    :param kind: The kind of the App. Possible values include: "app", "functionapp"

    :param server_farm_id: Resource ID of the associated App Service Plan, formatted as:
        "/subscriptions/{subscriptionID}/resourceGroups/{groupName}/providers/Microsoft.Web/serverfarms/{appServicePlanName}"

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.create_or_update test_name test_site test_group

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

    try:
        envelope = await hub.exec.azurerm.utils.create_object_model(
            "web", "Site", kind=kind, server_farm_id=server_farm_id, **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        app = webconn.web_apps.create_or_update(
            name=name, resource_group_name=resource_group, site_envelope=envelope,
        )

        app.wait()
        result = app.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (ValidationError, DefaultErrorResponseException) as exc:
        result = {"error": str(exc)}

    return result


async def create_function(
    hub, ctx, name, site, resource_group, **kwargs,
):
    """
    .. versionadded:: VERSION

    Create function for web site, or a deployment slot.

    :param name: The name of the function.

    :param site: The name of the site.
    
    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.create_function test_name test_site test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        envelope = await hub.exec.azurerm.utils.create_object_model(
            "web", "FunctionEnvelope", **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        function = webconn.web_apps.create_function(
            name=site,
            function_name=name,
            resource_group_name=resource_group,
            function_envelope=envelope,
        )

        function.wait()
        result = function.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except (ValidationError, DefaultErrorResponseException) as exc:
        result = {"error": str(exc)}

    return result


async def delete(
    hub,
    ctx,
    name,
    resource_group,
    delete_metrics=None,
    delete_empty_server_farm=None,
    **kwargs,
):
    """
    .. versionadded:: VERSION

    Deletes a web, mobile, or API app, or one of the deployment slots.

    :param name: The name of the App to delete.

    :param resource_group: The name of the resource group.

    :param delete_metrics: If true, web app metrics are also deleted.

    :param delete_empty_server_farm: Specify false if you want to keep empty App Service plan. By default, empty App
        Service plan is deleted.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.delete test_name test_group

    """
    result = False
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        plan = webconn.web_apps.delete(
            name=name,
            resource_group_name=resource_group,
            delete_metrics=delete_metrics,
            delete_empty_server_farm=delete_empty_server_farm,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Gets the details of a web, mobile, or API app.

    :param name: The name of the App.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.get test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        app = webconn.web_apps.get(name=name, resource_group_name=resource_group)

        if app:
            result = app.as_dict()
        else:
            result = {"error": "The specified web, mobile, or API app does not exist."}
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_app_settings_key_vault_references(
    hub, ctx, name, resource_group, **kwargs
):
    """
    .. versionadded:: VERSION

    Gets the config reference app settings and status of an app.

    :param name: The name of the App.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.get_app_settings_key_vault_references test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        app = webconn.web_apps.get_app_settings_key_vault_references(
            name=name, resource_group_name=resource_group
        )

        result = app.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except DefaultErrorResponseException as exc:
        result = {"error": str(exc)}

    return result


async def get_configuration(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Gets the configuration of an app, such as platform version and bitness, default documents, virtual applications,
        Always On, etc.

    :param name: The name of the App.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.get_configuration test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        app = webconn.web_apps.get_configuration(
            name=name, resource_group_name=resource_group
        )

        result = app.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except DefaultErrorResponseException as exc:
        result = {"error": str(exc)}

    return result


async def get_function(hub, ctx, name, site, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Get function information by its ID for web site, or a deployment slot.

    :param name: The name of the function

    :param site: The name of the site.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.get_function test_name test_site test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        func = webconn.web_apps.get_function(
            function_name=name, name=site, resource_group_name=resource_group
        )

        if func:
            result = func.as_dict()
        else:
            result = {"error": "The specified function does not exist."}
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: VERSION

    Get all apps for a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.list

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        apps = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.web_apps.list()
        )

        for app in apps:
            result[app["name"]] = app
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except DefaultErrorResponseException as exc:
        result = {"error": str(exc)}

    return result


async def list_by_resource_group(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Gets all web, mobile, and API apps in the specified resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.list_by_resource_group test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        apps = await hub.exec.azurerm.utils.paged_object_to_list(
            webconn.web_apps.list_by_resource_group(resource_group_name=resource_group)
        )

        for app in apps:
            result[app["name"]] = apps
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except DefaultErrorResponseException as exc:
        result = {"error": str(exc)}

    return result


async def list_application_settings(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: VERSION

    Gets the application settings of an app.

    :param name: The name of the app.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.web.app.list_application_settings test_name test_group

    """
    result = {}
    webconn = await hub.exec.azurerm.utils.get_client(ctx, "web", **kwargs)

    try:
        settings = webconn.web_apps.list_application_settings(
            name=name, resource_group_name=resource_group
        )

        result = settings.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("web", str(exc), **kwargs)
        result = {"error": str(exc)}
    except DefaultErrorResponseException as exc:
        result = {"error": str(exc)}

    return result
