# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Diagnostic Setting State Module

.. versionadded:: 2.0.0

.. versionchanged: 4.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed via acct. Note that the
    authentication parameters are case sensitive.

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

    Example acct setup for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            default:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass

    The authentication parameters can also be passed as a dictionary of keyword arguments to the ``connection_auth``
    parameter of each state, but this is not preferred and could be deprecated in the future.

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging
from operator import itemgetter

log = logging.getLogger(__name__)


async def present(
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
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Ensure a diagnostic setting exists. At least one destination for the diagnostic setting logs is required. Any
    combination of the following destinations is acceptable:

    1. Archive the diagnostic settings to a storage account. This would require the ``storage_account_id`` parameter.
    2. Stream the diagnostic settings to an event hub. This would require the ``event_hub_name`` and
    ``event_hub_authorization_rule_id`` parameters.
    3. Send the diagnostic settings to Log Analytics. This would require the ``workspace_id`` parameter.

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

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure diagnostic setting exists:
            azurerm.monitor.diagnostic_setting.present:
                - name: my_setting
                - resource_uri: my_resource
                - metrics:
                  - category: my_category
                    enabled: True
                    retention_policy:
                      enabled: True
                      days: 10
                - logs:
                  - category: my_category
                    enabled: True
                - storage_account_id: my_account_id

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    setting = await hub.exec.azurerm.monitor.diagnostic_setting.get(
        ctx, name, resource_uri, azurerm_log_level="info", **connection_auth
    )

    if "error" not in setting:
        action = "update"
        # Checks for changes in the metrics parameter
        if len(metrics) == len(setting.get("metrics", [])):
            new_metrics_sorted = sorted(metrics, key=itemgetter("category", "enabled"))
            old_metrics_sorted = sorted(
                setting.get("metrics", []), key=itemgetter("category", "enabled")
            )
            for index, metric in enumerate(new_metrics_sorted):
                changes = differ.deep_diff(old_metrics_sorted[index], metric)
                if changes:
                    ret["changes"]["metrics"] = {
                        "old": setting.get("metrics", []),
                        "new": metrics,
                    }
                    break
        else:
            ret["changes"]["metrics"] = {
                "old": setting.get("metrics", []),
                "new": metrics,
            }

        # Checks for changes in the logs parameter
        if len(logs) == len(setting.get("logs", [])):
            new_logs_sorted = sorted(logs, key=itemgetter("category", "enabled"))
            old_logs_sorted = sorted(
                setting.get("logs", []), key=itemgetter("category", "enabled")
            )
            for index, log in enumerate(new_logs_sorted):
                changes = differ.deep_diff(old_logs_sorted[index], log)
                if changes:
                    ret["changes"]["logs"] = {
                        "old": setting.get("logs", []),
                        "new": logs,
                    }
                    break
        else:
            ret["changes"]["logs"] = {"old": setting.get("logs", []), "new": logs}
        if storage_account_id:
            if storage_account_id != setting.get("storage_account_id", None):
                ret["changes"]["storage_account_id"] = {
                    "old": setting.get("storage_account_id"),
                    "new": storage_account_id,
                }

        if workspace_id:
            if workspace_id != setting.get("workspace_id", None):
                ret["changes"]["workspace_id"] = {
                    "old": setting.get("workspace_id"),
                    "new": workspace_id,
                }

        if event_hub_authorization_rule_id:
            if event_hub_authorization_rule_id != setting.get(
                "event_hub_authorization_rule_id", None
            ):
                ret["changes"]["event_hub_authorization_rule_id"] = {
                    "old": setting.get("event_hub_authorization_rule_id"),
                    "new": event_hub_authorization_rule_id,
                }

        if event_hub_name:
            if event_hub_name != setting.get("event_hub_name", None):
                ret["changes"]["event_hub_name"] = {
                    "old": setting.get("event_hub_name"),
                    "new": event_hub_name,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Diagnostic setting {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Diagnostic setting {0} would be updated.".format(name)
            return ret

    if ctx["test"]:
        ret["comment"] = "Diagnostic setting {0} would be created.".format(name)
        ret["result"] = None
        return ret

    setting_kwargs = kwargs.copy()
    setting_kwargs.update(connection_auth)

    setting = await hub.exec.azurerm.monitor.diagnostic_setting.create_or_update(
        ctx=ctx,
        name=name,
        resource_uri=resource_uri,
        logs=logs,
        metrics=metrics,
        storage_account_id=storage_account_id,
        workspace_id=workspace_id,
        log_analytics_destination_type=log_analytics_destination_type,
        event_hub_name=event_hub_name,
        event_hub_authorization_rule_id=event_hub_authorization_rule_id,
        **setting_kwargs,
    )

    if action == "create":
        ret["changes"] = {"old": {}, "new": setting}

    if "error" not in setting:
        ret["result"] = True
        ret["comment"] = f"Diagnostic setting {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} diagnostic setting {1}! ({2})".format(
        action, name, setting.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_uri, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a diagnostic setting does not exist for the specified resource uri.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure diagnostic setting is absent:
            azurerm.monitor.diagnostic_setting.absent:
                - name: my_setting
                - resource_uri: my_resource

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    setting = await hub.exec.azurerm.monitor.diagnostic_setting.get(
        ctx, name, resource_uri, azurerm_log_level="info", **connection_auth
    )

    if "error" in setting:
        ret["result"] = True
        ret["comment"] = "Diagnostic setting {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Diagnostic setting {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": setting,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.monitor.diagnostic_setting.delete(
        ctx, name, resource_uri, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Diagnostic setting {0} has been deleted.".format(name)
        ret["changes"] = {"old": setting, "new": {}}
        return ret

    ret["comment"] = "Failed to delete diagnostic setting {0}!".format(name)
    return ret
