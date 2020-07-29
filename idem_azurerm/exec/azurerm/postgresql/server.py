# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) PostgreSQL Server Operations Execution Module

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
import datetime

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.rdbms.postgresql.models  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import ValidationError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create(
    hub,
    ctx,
    name,
    resource_group,
    location,
    sku=None,
    version=None,
    ssl_enforcement=None,
    storage_profile=None,
    login=None,
    login_password=None,
    create_mode="Default",
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Creates a new server, or will overwrite an existing server.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param location: The location the resource resides in.

    :param sku: The name of the SKU (pricing tier) of the server. Typically, the name of the sku is in the form
        tier_family_cores, e.g. B_Gen4_1, GP_Gen5_8.

    :param version: Server version. Possible values include: '9.5', '9.6', '10', '10.0', '10.2', '11'.

    :param ssl_enforcement: Enable ssl enforcement or not when connect to server.
        Possible values include: 'Enabled', 'Disabled'.

    :param storage_profile: A dictionary representing the storage profile of a server. Parameters include:
        - ``backup_retention_days``: Backup retention days for the server.
        - ``geo_redundant_backup``: Enable Geo-redundant or not for server backup. Possible values include:
            'Enabled', 'Disabled'.
        - ``storage_mb``: Max storage allowed for a server.
        - ``storage_autogrow``: Enable Storage Auto Grow. Possible values include: 'Enabled', 'Disabled'

    :param login: The administrator's login name of a server. Can only be specified when the server is being created
        (and is required for creation).

    :param login_password: The password of the administrator login.

    :param tags: Application-specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.create test_name test_group test_location test_sku

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    if sku and not isinstance(sku, dict):
        sku = {"name": sku}

    try:
        propsmodel = await hub.exec.azurerm.utils.create_object_model(
            "rdbms.postgresql",
            "ServerPropertiesForDefaultCreate",
            version=version,
            ssl_enforcement=ssl_enforcement,
            storage_profile=storage_profile,
            create_mode=create_mode,
            administrator_login=login,
            administrator_login_password=login_password,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        servermodel = await hub.exec.azurerm.utils.create_object_model(
            "rdbms.postgresql",
            "ServerForCreate",
            sku=sku,
            location=location,
            properties=propsmodel,
            tags=tags,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        server = postconn.servers.create(
            server_name=name, resource_group_name=resource_group, parameters=servermodel
        )

        server.wait()
        result = server.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}
    except ValidationError as exc:
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes a server.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.delete test_name test_group

    """
    result = False
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        server = postconn.servers.delete(
            server_name=name, resource_group_name=resource_group,
        )

        server.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets information about a server.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.get test_name test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        server = postconn.servers.get(
            server_name=name, resource_group_name=resource_group,
        )

        result = server.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.0.0

    List all the servers in a given subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.list

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        servers = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.servers.list()
        )

        for server in servers:
            result[server["name"]] = server
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_resource_group(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    List all the servers in a given resource group.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.list_by_resource_group test_group

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        servers = await hub.exec.azurerm.utils.paged_object_to_list(
            postconn.servers.list_by_resource_group(resource_group_name=resource_group)
        )

        for server in servers:
            result[server["name"]] = server
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def restart(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Restarts a server.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.restart test_name test_group

    """
    result = False
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    try:
        server = postconn.servers.restart(
            server_name=name, resource_group_name=resource_group,
        )

        server.wait()
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update(
    hub,
    ctx,
    name,
    resource_group,
    sku=None,
    version=None,
    ssl_enforcement=None,
    storage_profile=None,
    login_password=None,
    tags=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Creates a new server, or will overwrite an existing server.

    :param name: The name of the server.

    :param resource_group: The name of the resource group. The name is case insensitive.

    :param sku: The name of the SKU (pricing tier) of the server. Typically, the name of the sku is in the form
        tier_family_cores, e.g. B_Gen4_1, GP_Gen5_8.

    :param version: Server version. Possible values include: '9.5', '9.6', '10', '10.0', '10.2', '11'.

    :param ssl_enforcement: Enable ssl enforcement or not when connect to server.
        Possible values include: 'Enabled', 'Disabled'.

    :param storage_profile: A dictionary representing the storage profile of a server. Parameters include:
        - ``backup_retention_days``: Backup retention days for the server.
        - ``geo_redundant_backup``: Enable Geo-redundant or not for server backup. Possible values include:
            'Enabled', 'Disabled'.
        - ``storage_mb``: Max storage allowed for a server.
        - ``storage_autogrow``: Enable Storage Auto Grow. Possible values include: 'Enabled', 'Disabled'

    :param login_password: The password of the administrator login.

    :param tags: Application-specific metadata in the form of key-value pairs.

    CLI Example:

    .. code-block:: bash

        azurerm.postgresql.server.update test_name test_group test_updated_params

    """
    result = {}
    postconn = await hub.exec.azurerm.utils.get_client(ctx, "postgresql", **kwargs)

    if sku and not isinstance(sku, dict):
        sku = {"name": sku}

    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "rdbms.postgresql",
            "ServerUpdateParameters",
            sku=sku,
            version=version,
            ssl_enforcement=ssl_enforcement,
            storage_profile=storage_profile,
            administrator_login_password=login_password,
            tags=tags,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        server = postconn.servers.update(
            server_name=name, resource_group_name=resource_group, parameters=paramsmodel
        )

        server.wait()
        result = server.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("postgresql", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
