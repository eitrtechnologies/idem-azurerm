# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Diagnostic Setting Execution Module

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
    import azure.mgmt.monitor.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.monitor.v2017_05_01_preview.models._models_py3 import (
        ErrorResponseException,
    )

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub,
    ctx,
    name,
    resource_uri,
    metrics,
    logs,
    workspace_id=None,
    log_analytics_destination_type=None,
    storage_account_id=None,
    event_hub_name=None,
    event_hub_authorization_rule_id=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    .. versionchanged:: 4.0.0

    Create or update diagnostic settings for the specified resource. At least one destination for the diagnostic
    setting logs is required. Any combination of the following destinations is acceptable:

    1. Archive the diagnostic settings to a storage account. This would require the ``storage_account_id`` paramater.
    2. Stream the diagnostic settings to an event hub. This would require the ``event_hub_name`` and
      ``event_hub_authorization_rule_id`` parameters.
    3. Send the diagnostic settings to a Log Analytics Workspace. This would require the ``workspace_id`` parameter.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    :param metrics: A list of dictionaries representing valid MetricSettings objects. If this list is empty,
        then the list passed as the logs parameter must have at least one element. Valid parameters are:

        - ``category``: Name of a diagnostic metric category for the resource type this setting is applied to. To obtain
          the list of diagnostic metric categories for a resource, first perform a GET diagnostic setting operation.
          This is a required parameter.
        - ``enabled``: A value indicating whether this category is enabled. This is a required parameter.
        - ``time_grain``: An optional timegrain of the metric in ISO-8601 format.
        - ``retention_policy``: An optional dictionary representing a RetentionPolicy object for the specified category.
          The default retention policy for a diagnostic setting is {'enabled': False, 'days': 0}. Required parameters
          include:

            - ``days``: The number of days for the retention in days. A value of 0 will retain the events indefinitely.
            - ``enabled``: A value indicating whether the retention policy is enabled.

    :param logs: A list of dictionaries representing valid LogSettings objects. If this list is empty, then
        the list passed as the metrics parameter must have at least one element. Valid parameters are:

        - ``category``: Name of a diagnostic log category for the resource type this setting is applied to. To obtain
          the list of diagnostic log categories for a resource, first perform a GET diagnostic setting operation.
          This is a required parameter.
        - ``enabled``: A value indicating whether this category is enabled. This is a required parameter.
        - ``retention_policy``: An optional dictionary representing a RetentionPolicy object for the specified category.
          The default retention policy for a diagnostic setting is {'enabled': False, 'days': 0}. Required parameters
          include:

          - ``days``: The number of days for the retention in days. A value of 0 will retain the events indefinitely.
          - ``enabled``: A value indicating whether the retention policy is enabled.

    :param workspace_id: The resource ID of the Log Analytics workspace to which you would like to send Diagnostic Logs.
        Required if you want to send the diagnostic settings data to Log Analytics.

    :param log_analytics_destination_type: A string indicating whether the export to the Log Analytics Workspace
        should store the logs within the legacy default destination type, the AzureDiagnostics table, or a dedicated,
        resource specific table. Optional, used with the ``workspace_id`` parameter. Possible values include:
        "Dedicated" and "AzureDiagnostics".

    :param storage_account_id: The resource ID of the storage account to which you would like to send Diagnostic Logs.
        Required if you want to archive the diagnostic settings data to a storage account.

    :param event_hub_name: The name of the event hub. If none is specified, the default event hub will be selected.
        Required to stream the diagnostic settings data to an event hub.

    :param event_hub_authorization_rule_id: The resource ID for the event hub authorization rule. Required with the
        ``event_hub_name`` parameter.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.create_or_update test_name test_uri test_metrics test_logs test_destination

    """
    result = {}
    moniconn = await hub.exec.azurerm.utils.get_client(ctx, "monitor", **kwargs)

    try:
        diagmodel = await hub.exec.azurerm.utils.create_object_model(
            "monitor",
            "DiagnosticSettingsResource",
            metrics=metrics,
            logs=logs,
            workspace_id=workspace_id,
            log_analytics_destination_type=log_analytics_destination_type,
            storage_account_id=storage_account_id,
            event_hub_authorization_rule_id=event_hub_authorization_rule_id,
            event_hub_name=event_hub_name,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        diag = moniconn.diagnostic_settings.create_or_update(
            name=name, resource_uri=resource_uri, parameters=diagmodel
        )

        result = diag.as_dict()
    except (CloudError, ErrorResponseException, SerializationError) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("monitor", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_uri, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes existing diagnostic settings for the specified resource.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.delete test_name test_uri

    """
    result = False
    moniconn = await hub.exec.azurerm.utils.get_client(ctx, "monitor", **kwargs)
    try:
        diag = moniconn.diagnostic_settings.delete(
            name=name, resource_uri=resource_uri, **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("monitor", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_uri, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the active diagnostic settings for the specified resource.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.get test_name test_uri

    """
    result = {}
    moniconn = await hub.exec.azurerm.utils.get_client(ctx, "monitor", **kwargs)

    try:
        diag = moniconn.diagnostic_settings.get(
            name=name, resource_uri=resource_uri, **kwargs
        )

        result = diag.as_dict()
    except (CloudError, ErrorResponseException) as exc:
        await hub.exec.azurerm.utils.log_cloud_error("monitor", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_uri, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets the active diagnostic settings list for the specified resource.

    :param resource_uri: The identifier of the resource.

    CLI Example:

    .. code-block:: bash

        azurerm.monitor.diagnostic_setting.list test_uri

    """
    result = {}
    moniconn = await hub.exec.azurerm.utils.get_client(ctx, "monitor", **kwargs)

    try:
        diag = moniconn.diagnostic_settings.list(resource_uri=resource_uri, **kwargs)

        values = diag.as_dict().get("value", [])
        for value in values:
            result[value["name"]] = value
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("monitor", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
