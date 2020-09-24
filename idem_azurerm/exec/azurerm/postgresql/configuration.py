# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Configuration Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.rdbms.postgresql.models  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, server_name, resource_group, value, **kwargs
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 4.0.0

    Updates the specified configuration setting for the given server. A list of configuration settings that can be
    updated for the given server can be found by using the list_by_server operation below. Additionally, all
    possible values for each individual configuration setting can be found using that module.

    :param name: The name of the server configuration setting to update.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param value: The value of the configuration setting.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.configuration.create_or_update test_name test_server test_group test_value

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        config = postconn.configurations.create_or_update(
            configuration_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
            value=value,
        )

        config.wait()
        result = config.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets information about a configuration setting for the specified server.

    :param name: The name of the server configuration setting.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.configuration.get test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        config = postconn.configurations.get(
            configuration_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
        )

        result = config.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_server(hub, ctx, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    List all the configuration settings in a given server.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.configuration.list_by_server test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        configs = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.configurations.list_by_server(
                server_name=server_name, resource_group_name=resource_group
            )
        )

        for config in configs:
            result[config["name"]] = config
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
