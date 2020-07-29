# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Security Alert Policy Operations State Module

.. versionadded:: 2.0.0

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

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud. Possible values:
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
import logging

log = logging.getLogger(__name__)

TREQ = {
    "present": {
        "require": [
            "states.azurerm.resource.group.present",
            "states.azurerm.postgresql.server.present",
        ]
    }
}


async def present(
    hub,
    ctx,
    server_name,
    resource_group,
    policy_state,
    disabled_alerts=None,
    email_addresses=None,
    email_account_admins=None,
    storage_endpoint=None,
    storage_account_access_key=None,
    retention_days=None,
    force_access_key=False,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensures that the specified server security alert policy exists within the given PostgreSQL server.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param policy_state: Specifies the state of the policy, whether it is enabled or disabled. Possible values include:
        'Enabled', 'Disabled'.

    :param disabled_alerts: Specifies an array of alerts that are disabled. Possible values are: 'Sql_Injection',
        'Sql_Injection_Vulnerability', and 'Access_Anomaly'. It is important to note that the default value of this
        parameter is [''].

    :param email_addresses: Specifies an array of e-mail addresses to which the alert is sent. It is important to note
        that the default value of this parameter is [''].

    :param email_account_admins: A boolean value that specifies whether the alert is sent to the account
        administrators or not.

    :param storage_endpoint: Specifies the blob storage endpoint (e.g. https://MyAccount.blob.core.windows.net).
        This blob storage will hold all Threat Detection audit logs.

    :param storage_account_access_key: Specifies the identifier key of the Threat Detection audit storage account.

    :param retention_days: Specifies the number of days to keep in the Threat Detection audit logs.

    :param force_access_key: A Boolean flag that represents whether or not the storage account access ket value should
        be updated. If it is set to True, then the password will be updated if the server already exists. If it is set
        to False, then the password will not be updated unless other parameters also need to be updated.
        Defaults to False.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure server security alert policy exists:
            azurerm.postgresql.server_security_alert_policy.present:
                - server_name: my_server
                - resource_group: my_rg
                - policy_state: 'Enabled'
                - connection_auth: {{ profile }}

    """
    name = "Default"

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

    policy = await hub.exec.azurerm.postgresql.server_security_alert_policy.get(
        ctx=ctx,
        server_name=server_name,
        resource_group=resource_group,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in policy:
        action = "update"
        if policy_state != policy.get("state"):
            ret["changes"]["state"] = {"old": policy.get("state"), "new": policy_state}

        if disabled_alerts:
            if sorted(disabled_alerts or [""]) != sorted(
                policy.get("disabled_alerts", [""])
            ):
                ret["changes"]["disabled_alerts"] = {
                    "old": policy.get("disabled_alerts", [""]),
                    "new": (disabled_alerts or [""]),
                }

        if email_addresses:
            if sorted(email_addresses or [""]) != sorted(
                policy.get("email_addresses", [""])
            ):
                ret["changes"]["email_addresses"] = {
                    "old": policy.get("email_addresses", [""]),
                    "new": (email_addresses or [""]),
                }

        if storage_endpoint:
            if storage_endpoint != policy.get("storage_endpoint"):
                ret["changes"]["storage_endpoint"] = {
                    "old": policy.get("storage_endpoint"),
                    "new": storage_endpoint,
                }

        if email_account_admins is not None:
            if email_account_admins != policy.get("email_account_admins"):
                ret["changes"]["email_account_admins"] = {
                    "old": policy.get("email_account_admins"),
                    "new": email_account_admins,
                }

        if retention_days is not None:
            if retention_days != policy.get("retention_days"):
                ret["changes"]["retention_days"] = {
                    "old": policy.get("retention_days"),
                    "new": retention_days,
                }

        if storage_account_access_key:
            if force_access_key:
                ret["changes"]["storage_account_access_key"] = {"new": "REDACTED"}
            elif ret["changes"]:
                ret["changes"]["storage_account_access_key"] = {"new": "REDACTED"}

        if not ret["changes"]:
            ret["result"] = True
            ret[
                "comment"
            ] = "The server security alert policy {0} for the server {1} is already present.".format(
                name, server_name
            )
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "The server security alert policy {0} for the server {1} would be updated.".format(
                name, server_name
            )
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "server_name": server_name,
                "resource_group": resource_group,
                "state": policy_state,
            },
        }

        if disabled_alerts:
            ret["changes"]["new"]["disabled_alerts"] = disabled_alerts
        if email_addresses:
            ret["changes"]["new"]["email_addresses"] = email_addresses
        if email_account_admins is not None:
            ret["changes"]["new"]["email_account_admins"] = email_account_admins
        if storage_endpoint:
            ret["changes"]["new"]["storage_endpoint"] = storage_endpoint
        if storage_account_access_key:
            ret["changes"]["new"]["storage_account_access_key"] = "REDACTED"
        if retention_days is not None:
            ret["changes"]["new"]["retention_days"] = retention_days

    if ctx["test"]:
        ret[
            "comment"
        ] = "The server security alert policy {0} for the server {1} would be created.".format(
            name, server_name
        )
        ret["result"] = None
        return ret

    policy_kwargs = kwargs.copy()
    policy_kwargs.update(connection_auth)

    policy = await hub.exec.azurerm.postgresql.server_security_alert_policy.create_or_update(
        ctx=ctx,
        server_name=server_name,
        resource_group=resource_group,
        policy_state=policy_state,
        disabled_alerts=disabled_alerts,
        email_addresses=email_addresses,
        email_account_admins=email_account_admins,
        storage_endpoint=storage_endpoint,
        storage_account_access_key=storage_account_access_key,
        retention_days=retention_days,
        **policy_kwargs,
    )

    if "error" not in policy:
        ret["result"] = True
        ret[
            "comment"
        ] = f"The server security alert policy {name} for the server {server_name} has been {action}d."
        return ret

    ret[
        "comment"
    ] = "Failed to {0} the server security alert policy {1} for the server {2}! ({3})".format(
        action, name, server_name, policy.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret
