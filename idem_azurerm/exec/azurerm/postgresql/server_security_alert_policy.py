# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Security Alert Policy Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.rdbms.postgresql.models  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update(
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
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Creates or updates a threat detection policy.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param policy_state: Specifies the state of the policy, whether it is enabled or disabled. Possible values include:
        'Enabled', 'Disabled'.

    :param disabled_alerts: Specifies an array of alerts that are disabled. Possible values are: 'Sql_Injection',
        'Sql_Injection_Vulnerability', and 'Access_Anomaly'. It is import to note that the default value of this
        parameter is [''].

    :param email_addresses: Specifies an array of e-mail addresses to which the alert is sent. It is important to note
        that the default value of this parameter is [''].

    :param email_account_admins: A boolean value that specifies whether the alert is sent to the account
        administrators or not.

    :param storage_endpoint: Specifies the blob storage endpoint (e.g. https://MyAccount.blob.core.windows.net).
        This blob storage will hold all Threat Detection audit logs.

    :param storage_account_access_key: Specifies the identifier key of the Threat Detection audit storage account.

    :param retention_days: Specifies the number of days to keep in the Threat Detection audit logs.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server_security_alert_policy.create_or_update test_server test_group test_state

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "rdbms.postgresql",
            "ServerSecurityAlertPolicy",
            state=policy_state,
            disabled_alerts=disabled_alerts,
            email_addresses=email_addresses,
            email_account_admins=email_account_admins,
            storage_endpoint=storage_endpoint,
            storage_account_access_key=storage_account_access_key,
            retention_days=retention_days,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        policy = postconn.server_security_alert_policies.create_or_update(
            server_name=server_name,
            resource_group_name=resource_group,
            parameters=paramsmodel,
        )

        policy.wait()
        result = policy.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Get a server's security alert policy.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server_security_alert_policy.get test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        policy = postconn.server_security_alert_policies.get(
            server_name=server_name, resource_group_name=resource_group,
        )

        result = policy.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
