# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Database Operations Execution Module

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
    hub, ctx, name, server_name, resource_group, charset=None, collation=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Creates a new database or updates an existing database.

    :param name: The name of the database.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param charset: The charset of the database. Defaults to None.

    :param collation: The collation of the database. Defaults to None.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.database.create_or_update test_name test_server test_group test_charset test_collation

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        database = postconn.databases.create_or_update(
            database_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
            charset=charset,
            collation=collation,
        )

        database.wait()
        result = database.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes a database.

    :param name: The name of the database.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.database.delete test_name test_server test_group

    """
    result = False
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        database = postconn.databases.delete(
            database_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
        )

        database.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets information about a database.

    :param name: The name of the database.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.database.get test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        database = postconn.databases.get(
            database_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
        )

        result = database.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_server(hub, ctx, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    List all the databases in a given server.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.database.list_by_server test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        databases = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.databases.list_by_server(
                server_name=server_name, resource_group_name=resource_group
            )
        )

        for database in databases:
            result[database["name"]] = database
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
