# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Application Insights Component Operations Execution Module

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
    hub,
    ctx,
    name,
    resource_group,
    kind,
    application_type,
    retention=None,
    immediate_purge_data=None,
    disable_ip_masking=None,
    ingestion_public_network_access=None,
    query_public_network_access=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates (or updates) an Application Insights component.

    :param name: The name of the Application Insights component resource.

    :param resource_group: The name of the resource group.

    :param kind: The kind of application that this component refers to, used to customize UI. This value is a freeform
        string, values should typically be one of the following: "web", "ios", "other", "store", "java", "phone".

    :param application_type: Type of application being monitored. Possible values include: 'web', 'other'.
        Default to "web".

    :param retention: Retention period in days. Defaults to 90.

    :param immediate_purge_data: A boolean value representing whether or not data should be purged immediately after
        30 days.

    :param disable_ip_masking: Disable IP masking.

    :param tags: A dictionary of strings can be passed as tag metadata to the Application Insights Component object.

    CLI Example:

    .. code-block:: bash

        azurerm.application_insights.component.create_or_update test_name test_group "web" "web"

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
    insightconn = await hub.exec.azurerm.utils.get_client(
        ctx, "applicationinsights", **kwargs
    )

    try:
        componentmodel = await hub.exec.azurerm.utils.create_object_model(
            "applicationinsights",
            "ApplicationInsightsComponent",
            kind=kind,
            application_type=application_type,
            tags=tags,
            retention_in_days=retention,
            immediate_purge_data_on30_days=immediate_purge_data,
            disable_ip_masking=disable_ip_masking,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        component = insightconn.components.create_or_update(
            resource_name=name,
            resource_group_name=resource_group,
            insight_properties=componentmodel,
        )

        result = component.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "applicationinsights", str(exc), **kwargs
        )
        result = {"error": str(exc)}
    except ValidationError as exc:
        result = {"error": str(exc)}

    return result


async def delete(
    hub, ctx, name, resource_group, **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Deletes an Application Insights component.

    :param name: The name of the component to delete.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.application_insights.component.delete test_name test_group

    """
    result = False
    insightconn = await hub.exec.azurerm.utils.get_client(
        ctx, "applicationinsights", **kwargs
    )

    try:
        component = insightconn.components.delete(
            resource_name=name, resource_group_name=resource_group,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "applicationinsights", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 3.0.0

    Returns an Application Insights component.

    :param name: The name of the component.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.application_insights.component.get test_name test_group

    """
    result = {}
    insightconn = await hub.exec.azurerm.utils.get_client(
        ctx, "applicationinsights", **kwargs
    )

    try:
        component = insightconn.components.get(
            resource_name=name, resource_group_name=resource_group
        )

        result = component.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "applicationinsights", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Gets a list of all Application Insights components within a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        azurerm.application_insights.component.list

    """
    result = {}
    insightconn = await hub.exec.azurerm.utils.get_client(
        ctx, "applicationinsights", **kwargs
    )

    try:
        if resource_group:
            components = await hub.exec.azurerm.utils.paged_object_to_list(
                insightconn.components.list_by_resource_group(
                    resource_group_name=resource_group
                )
            )
        else:
            components = await hub.exec.azurerm.utils.paged_object_to_list(
                insightconn.components.list()
            )

        for component in components:
            result[component["name"]] = component
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "applicationinsights", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
