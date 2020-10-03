# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Key Operations Execution Module

.. versionadded:: 4.0.0

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

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, server_name, resource_group, key_uri, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Creates or updates a PostgreSQL Server key.

    :param name: The name of the PostgreSQL Server key to be operated on (updated or created).

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param key_uri: The URI of the key.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server_key.create_or_update test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        key = postconn.server_keys.create_or_update(
            key_name=name,
            server_name=server_name,
            resource_group_name=resource_group,
            uri=key_uri,
        )

        key.wait()
        result = key.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}
    except AttributeError as exc:
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Deletes the PostgreSQL Server key with the given name.

    :param name: The name of the PostgreSQL Server key to be deleted.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server_key.delete test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        key = postconn.server_keys.delete(
            key_name=name, server_name=server_name, resource_group_name=resource_group,
        )

        key.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a PostgreSQL Server key.

    :param name: The name of the PostgreSQL Server key to be retrieved.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server_key.get test_name test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        key = postconn.server_keys.get(
            key_name=name, server_name=server_name, resource_group_name=resource_group,
        )

        result = key.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, server_name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets a list of Server keys.

    :param server_name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server_key.list test_server test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        keys = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.server_keys.list(
                server_name=server_name, resource_group_name=resource_group
            )
        )

        for key in keys:
            result[key["name"]] = key
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
