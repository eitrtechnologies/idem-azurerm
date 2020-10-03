# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Virtual Network Rule Operations Execution Module

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
    name,
    server_name,
    resource_group,
    subnet_id,
    ignore_missing_endpoint=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Creates or updates an existing virtual network rule.

    :param name: The name of the virtual network rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param subnet_id: The ARM Resource ID of the virtual network subnet. The ID will be in the following format:
        '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}/subnets/{subnetName}'

    :param ignore_missing_endpoint: (Optional) A boolean value representing whether the firewall rule is created before
        the virtual network has the vnet service endpoint enabled.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.virtual_network_rule.create_or_update test_name test_server test_group test_subnet

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rule = postconn.virtual_network_rules.create_or_update(
            virtual_network_rule_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
            virtual_network_subnet_id=subnet_id,
            ignore_missing_vnet_service_endpoint=ignore_missing_endpoint,
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

    Deletes the virtual network rule with the given name.

    :param name: The name of the virtual network rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.virtual_network_rule.delete test_name test_server test_group

    """
    result = False
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rule = postconn.virtual_network_rules.delete(
            virtual_network_rule_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
        )

        rule.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets a virtual network rule.

    :param name: The name of the virtual network rule.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.virtual_network_rule.get test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rule = postconn.virtual_network_rules.get(
            virtual_network_rule_name=name,
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

    Gets a list of virtual network rules in a server.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.virtual_network_rule.list_by_server test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        rules = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.virtual_network_rules.list_by_server(
                server_name=server_name, resource_group_name=resource_group
            )
        )

        for rule in rules:
            result[rule["name"]] = rule
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
