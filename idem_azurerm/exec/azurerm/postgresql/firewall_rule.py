# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Firewall Rule Operations Execution Module

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
    from msrest.exceptions import ValidationError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update(
    hub,
    ctx,
    name,
    server_name,
    resource_group,
    start_ip_address,
    end_ip_address,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Creates a new firewall rule or updates an existing firewall rule.

    :param name: The name of the server firewall rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param start_ip_address: The start IP address of the server firewall rule. Must be IPv4 format.

    :param end_ip_address: The end IP address of the server firewall rule. Must be IPv4 format.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.firewall_rule.create_or_update test_name test_server test_group test_start test_end

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rule = postconn.firewall_rules.create_or_update(
            firewall_rule_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
            start_ip_address=start_ip_address,
            end_ip_address=end_ip_address,
        )

        rule.wait()
        result = rule.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes a server firewall rule.

    :param name: The name of the server firewall rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.firewall_rule.delete test_name test_server test_group

    """
    result = False
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        server = postconn.firewall_rules.delete(
            firewall_rule_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
        )

        server.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets information about a server firewall rule.

    :param name: The name of the server firewall rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.firewall_rule.get test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rule = postconn.firewall_rules.get(
            firewall_rule_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
        )

        result = rule.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_server(hub, ctx, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    List all the firewall rules in a given server.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.firewall_rule.list_by_server test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rules = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.firewall_rules.list_by_server(
                server_name=server_name, resource_group_name=resource_group
            )
        )

        for rule in rules:
            result[rule["name"]] = rule
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
