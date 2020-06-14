# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Redis Operations State Module

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
from dict_tools import differ
import logging

log = logging.getLogger(__name__)

TREQ = {"present": {"require": ["states.azurerm.resource.group.present",]}}


async def present(
    hub,
    ctx,
    name,
    resource_group,
    location,
    sku,
    redis_configuration=None,
    enable_non_ssl_port=False,
    tenant_settings=None,
    shard_count=None,
    minimum_tls_version=None,
    subnet_id=None,
    static_ip=None,
    zones=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a redis cache exists in the resource group.

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

    :param tags: A dictionary of strings can be passed as tag metadata to the storage account object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure redis cache exists:
            azurerm.redis.operations.present:
                - name: my_account
                - resource_group: my_rg
                - sku:
                    name: 'Premium'
                    family: 'P'
                    capacity: 3
                - location: 'eastus'
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

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

    cache = await hub.exec.azurerm.redis.operations.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in cache:
        action = "update"

        if tags:
            tag_changes = differ.deep_diff(cache.get("tags", {}), tags)
            if tag_changes:
                ret["changes"]["tags"] = tag_changes

        sku_changes = differ.deep_diff(cache.get("sku"), sku)
        if sku_changes:
            ret["changes"]["sku"] = sku_changes

        if tenant_settings:
            tenant_changes = differ.deep_diff(
                cache.get("tenant_settings", {}), tenant_settings
            )
            if tenant_changes:
                ret["changes"]["tenant_settings"] = tenant_changes

        if redis_configuration:
            config_changes = differ.deep_diff(
                cache.get("redis_configuration", {}), redis_configuration
            )
            if config_changes:
                ret["changes"]["redis_configuration"] = config_changes

        if enable_non_ssl_port is not None:
            if enable_non_ssl_port != cache.get("enable_non_ssl_port"):
                ret["changes"]["enable_non_ssl_port"] = {
                    "old": cache.get("enable_non_ssl_port"),
                    "new": enable_non_ssl_port,
                }
        if shard_count is not None:
            if shard_count != cache.get("shard_count", 0):
                ret["changes"]["shard_count"] = {
                    "old": cache.get("shard_count"),
                    "new": shard_count,
                }

        if minimum_tls_version:
            if minimum_tls_version != cache.get("minimum_tls_version"):
                ret["changes"]["minimum_tls_version"] = {
                    "old": cache.get("minimum_tls_version"),
                    "new": minimum_tls_version,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Redis cache {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Redis cache {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "sku": sku,
                "location": location,
            },
        }

        if tags:
            ret["changes"]["new"]["tags"] = tags
        if redis_configuration:
            ret["changes"]["new"]["redis_configuration"] = redis_configuration
        if enable_non_ssl_port is not None:
            ret["changes"]["new"]["enable_non_ssl_port"] = enable_non_ssl_port
        if tenant_settings:
            ret["changes"]["new"]["tenant_settings"] = tenant_settings
        if shard_count is not None:
            ret["changes"]["new"]["shard_count"] = shard_count
        if minimum_tls_version:
            ret["changes"]["new"]["minimum_tls_version"] = minimum_tls_version
        if subnet_id:
            ret["changes"]["new"]["subnet_id"] = subnet_id
        if static_ip:
            ret["changes"]["new"]["static_ip"] = static_ip
        if zones:
            ret["changes"]["new"]["zones"] = zones

    if ctx["test"]:
        ret["comment"] = "Redis cache {0} would be created.".format(name)
        ret["result"] = None
        return ret

    cache_kwargs = kwargs.copy()
    cache_kwargs.update(connection_auth)

    if action == "create":
        cache = await hub.exec.azurerm.redis.operations.create(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
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
            tags=tags,
            **cache_kwargs,
        )
    else:
        cache = await hub.exec.azurerm.redis.operations.update(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            sku=sku,
            redis_configuration=redis_configuration,
            enable_non_ssl_port=enable_non_ssl_port,
            tenant_settings=tenant_settings,
            shard_count=shard_count,
            minimum_tls_version=minimum_tls_version,
            tags=tags,
            **cache_kwargs,
        )

    if "error" not in cache:
        ret["result"] = True
        ret["comment"] = f"Redis cache {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Redis cache {1}! ({2})".format(
        action, name, cache.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a Redis cache does not exist in the specified resource group.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure redis cache does not exist:
            azurerm.redis.operations.absent:
                - name: my_account
                - resource_group: my_rg
                - connection_auth: {{ profile }}

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

    cache = await hub.exec.azurerm.redis.operations.get(
        ctx, name, resource_group, **connection_auth
    )

    if "error" in cache:
        ret["result"] = True
        ret["comment"] = "Redis cache {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Redis cache {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": cache,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.redis.operations.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Redis cache {0} has been deleted.".format(name)
        ret["changes"] = {"old": cache, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Redis cache {0}!".format(name)
    return ret
