# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Redis Operations Execution Module

.. versionadded:: 2.0.0

.. versionchanged:: 3.0.0

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
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def check_name_availability(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 2.0.0

    Checks that the redis cache name is valid and is not already in use.

    :param name: The name of the Redis cache to check the availability of

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.check_name_availability test_name

    """
    result = False
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        avail = redconn.redis.check_name_availability(
            name=name, type="Microsoft.Cache/redis",
        )

        if avail is None:
            result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create(
    hub,
    ctx,
    name,
    resource_group,
    location,
    sku,
    redis_configuration=None,
    enable_non_ssl_port=None,
    tenant_settings=None,
    shard_count=None,
    minimum_tls_version=None,
    subnet_id=None,
    static_ip=None,
    zones=None,
    polling=True,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    .. versionchanged:: 3.0.0

    Create or replace (overwrite/recreate, with potential downtime) an existing Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param location: The geo-location where the resource lives.

    :param sku: A dictionary representing the SKU of the Redis cache to deploy. Required parameters include:
        - ``name``: The type of Redis cache to deploy. Possible values include: 'Basic', 'Standard', and 'Premium'.
        - ``family``: The SKU family to use. Possible values include 'C' for Basic/Standard and 'P' for Premium.
        - ``capacity``: The size of the Redis cache to deploy. Possible values include 0, 1, 2, 3, 4, 5, and 6 for the
                        C (Basic/Standard) family and 1, 2, 3, and 4 for the P (Premium) family.

    :param redis_configuration: A dictionary of string key-value pairs that represent all Redis Settings. Some possible
        keys include: rdb-backup-enabled, rdb-storage-connection-string, rdb-backup-frequency, maxmemory-delta,
        maxmemory-policy, notify-keyspace-events, maxmemory-samples, slowlog-log-slower-than, slowlog-max-len,
        list-max-ziplist-entries, list-max-ziplist-value, hash-max-ziplist-entries, hash-max-ziplist-value,
        set-max-intset-entries, zset-max-ziplist-entries, zset-max-ziplist-value, and more.

    :param enable_non_ssl_port: Specifies whether the non-ssl Redis server port (6379) is enabled. Defaults to False.

    :param tenant_settings: A dictionary of tenant settings.

    :param shard_count: The number of shards to be created on a Premium Cluster Cache.

    :param minimum_tls_version: The specified TLS version (or higher) that clients are required to use. Possible values
        include: '1.0', '1.1', and '1.2'.

    :param subnet_id: The full resource ID of a subnet in a virtual network to deploy the Redis cache in. Example
        format: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/Microsoft.{Network|ClassicNetwork}/VirtualNetworks/vnet1/subnets/subnet1

    :param static_ip: Static IP address. Required when deploying a Redis cache inside an existing Azure Virtual Network.

    :param zones: A list of availability zones denoting where the resource needs to come from.

    :param polling: A boolean flag representing whether a Poller will be used during the creation of the Redis Cache.
        If set to True, a Poller will be used by this operation and the module will not return until the Redis Cache
        has completed its creation process and has been successfully provisioned. If set to False, the module will
        return once the Redis Cache has successfully begun its creation process. Defaults to True.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.create test_name test_rg test_location test_sku

    """
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "redis",
            "RedisCreateParameters",
            sku=sku,
            location=location,
            redis_configuration=redis_configuration,
            enable_non_ssl_port=enable_non_ssl_port,
            tenant_settings=tenant_settings,
            shard_count=shard_count,
            minimum_tls_version=minimum_tls_version,
            subnet_id=subnet_id,
            static_ip=static_ip,
            zones=zones,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        cache = redconn.redis.create(
            name=name,
            resource_group_name=resource_group,
            parameters=paramsmodel,
            polling=polling,
        )

        cache.wait()
        result = cache.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Deletes a Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.delete test_name test_rg

    """
    result = False
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        cache = redconn.redis.delete(name=name, resource_group_name=resource_group)

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)

    return result


async def export_data(
    hub, ctx, name, resource_group, prefix, container, file_format=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Export data from the redis cache to blobs in a container.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param prefix: The prefix to use for exported files.

    :param container: The name of the container to export to.

    :param file_format: An optional file format.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.export_data test_name test_rg test_prefix test_container

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    # Create a ExportRDBParameters object
    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "redis",
            "ExportRDBParameters",
            prefix=prefix,
            container=container,
            format=file_format,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        cache = redconn.redis.export_data(
            name=name, resource_group_name=resource_group, parameters=paramsmodel
        )

        cache.wait()
        result = cache.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def force_reboot(
    hub, ctx, name, resource_group, reboot_type, shard_id=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Reboot specified Redis node(s). This operation requires write permission to the cache resource.
        There can be potential data loss.

    :param name: The name of the redis cache.

    :param resource_group: The name of the resource group.

    :param reboot_type: Which Redis node(s) to reboot. Depending on this value data loss is possible. Possible
        values include: 'PrimaryNode', 'SecondaryNode', 'AllNodes'.

    :param shard_id: If clustering is enabled, the ID of the shard to be rebooted.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.force_reboot test_name test_rg test_type test_id

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        cache = redconn.redis.force_reboot(
            name=name,
            resource_group_name=resource_group,
            reboot_type=reboot_type,
            shard_id=shard_id,
        )

        result = cache.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets a Redis cache (resource description).

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.get test_name test_rg

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        cache = redconn.redis.get(name=name, resource_group_name=resource_group)

        result = cache.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def import_data(
    hub, ctx, name, resource_group, files, file_format=None, **kwargs
):
    """
    .. versionadded:: 2.0.0

    Import data into Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param files: A list of strings that represent the names of files to import.

    :param file_format: An optional file format.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.import_data test_name test_rg test_files

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        cache = redconn.redis.import_data(
            name=name,
            resource_group_name=resource_group,
            files=files,
            format=file_format,
        )

        cache.wait()
        result = cache.result().as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets all Redis caches in the specified subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.list

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        caches = await hub.exec.azurerm.utils.paged_object_to_list(redconn.redis.list())

        for cache in caches:
            result[cache["name"]] = cache
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_resource_group(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Lists all Redis caches in a resource group.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.list_by_resource_group test_rg

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        caches = await hub.exec.azurerm.utils.paged_object_to_list(
            redconn.redis.list_by_resource_group(resource_group_name=resource_group,)
        )

        for cache in caches:
            result[cache["name"]] = cache
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_keys(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 2.0.0

    Retrieve a Redis cache's access keys. This operation requires write permission to the cache resource.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.list_keys test_name test_rg

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        keys = redconn.redis.list_keys(name=name, resource_group_name=resource_group)

        result = keys.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_upgrade_notifications(hub, ctx, name, resource_group, history, **kwargs):
    """
    .. versionadded:: 2.0.0

    Gets any upgrade notifications for a Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param history: A float representing how many minutes in past to look for upgrade notifications.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.list_upgrade_notifications test_name test_rg test_history

    """
    result = {}
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        notifications = redconn.redis.list_upgrade_notifications(
            name=name, resource_group_name=resource_group, history=history
        )

        result = notifications.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def regenerate_key(hub, ctx, name, resource_group, key_type, **kwargs):
    """
    .. versionadded:: 2.0.0

    Regenerate Redis cache's access keys. This operation requires write permission to the cache resource.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param key_type: The Redis access key to regenerate. Possible values include: 'Primary' and 'Secondary'.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.renegerate_key test_name test_rg test_type

    """
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        keys = redconn.redis.regenerate_key(
            resource_group_name=resource_group, name=name, key_type=key_type, **kwargs
        )

        result = keys.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def update(
    hub,
    ctx,
    name,
    resource_group,
    sku=None,
    redis_configuration=None,
    enable_non_ssl_port=None,
    tenant_settings=None,
    shard_count=None,
    minimum_tls_version=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Update an existing Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param sku: A dictionary representing the SKU of the Redis cache to deploy. Required parameters include:
        - ``name``: The type of Redis cache to deploy. Possible values include: 'Basic', 'Standard', and 'Premium'.
        - ``family``: The SKU family to use. Possible values include 'C' for Basic/Standard and 'P' for Premium.
        - ``capacity``: The size of the Redis cache to deploy. Possible values include 0, 1, 2, 3, 4, 5, and 6 for the
                        C (Basic/Standard) family and 1, 2, 3, and 4 for the P (Premium) family.

    :param redis_configuration: A dictionary of string key-value pairs that represent all Redis Settings. Some possible
        keys include: rdb-backup-enabled, rdb-storage-connection-string, rdb-backup-frequency, maxmemory-delta,
        maxmemory-policy, notify-keyspace-events, maxmemory-samples, slowlog-log-slower-than, slowlog-max-len,
        list-max-ziplist-entries, list-max-ziplist-value, hash-max-ziplist-entries, hash-max-ziplist-value,
        set-max-intset-entries, zset-max-ziplist-entries, zset-max-ziplist-value, and more.

    :param enable_non_ssl_port: Specifies whether the non-ssl Redis server port (6379) is enabled. Defaults to False.

    :param tenant_settings: A dictionary of tenant settings.

    :param shard_count: The number of shards to be created on a Premium Cluster Cache.

    :param minimum_tls_version: The specified TLS version (or higher) that clients are required to use. Possible values
        include: '1.0', '1.1', and '1.2'.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.operations.update test_name test_rg test_location test_sku

    """
    redconn = await hub.exec.azurerm.utils.get_client(ctx, "redis", **kwargs)

    try:
        paramsmodel = await hub.exec.azurerm.utils.create_object_model(
            "redis",
            "RedisUpdateParameters",
            sku=sku,
            redis_configuration=redis_configuration,
            enable_non_ssl_port=enable_non_ssl_port,
            tenant_settings=tenant_settings,
            shard_count=shard_count,
            minimum_tls_version=minimum_tls_version,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        cache = redconn.redis.update(
            name=name, resource_group_name=resource_group, parameters=paramsmodel
        )

        result = cache.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("redis", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result
