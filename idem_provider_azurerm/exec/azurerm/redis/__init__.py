# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Redis Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
    * `azure-mgmt-redis <https://pypi.org/project/azure-mgmt-redis>`_ >= 6.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.36.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.1
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function in order to work properly.

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

'''
# Python libs
from __future__ import absolute_import
import logging

try:
    from six.moves import range as six_range
except ImportError:
    six_range = range

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.network.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def check_name_availability(hub, name, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Checks that the redis cache name is valid and is not already in use.

    :param name: The name of the Redis cache to check the availability of

    CLI Example:

    .. code-block:: bash

        azurerm.redis.check_name_availability test_name

    '''
    result = False
    redconn = await hub.exec.utils.azurerm.get_client('redis', **kwargs)

    try:
        avail = redconn.redis.check_name_availability(
            name=name,
            type='Microsoft.Cache/redis',
        )

        if avail is None:
            result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('redis', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def create(hub, name, resource_group, PARAMETERS, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Create or replace (overwrite/recreate, with potential downtime) an existing Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    INSERT PARAMETERS HERE

    CLI Example:

    .. code-block:: bash

        azurerm.redis.create test_name test_group

    '''
    pass


async def delete(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Deletes a Redis cache.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.
    
    CLI Example:

    .. code-block:: bash

        azurerm.redis.delete test_name test_rg

    '''
    result = False
    redconn = await hub.exec.utils.azurerm.get_client('redis', **kwargs)

    try:
        cache = redconn.redis.delete(
            name=name,
            resource_group_name=resource_group
        )

        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('redis', str(exc), **kwargs)

    return result


async def export_data(hub, name, resource_group, prefix, container, format=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Export data from the redis cache to blobs in a container.

    :param name: The name of the Redis cache.

    :param resource_group: The name of the resource group.

    :param prefix: The prefix to use for exported files.

    :param container: The container name to export to.

    :param format: An optional file format.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.export_data test_name test_rg test_prefix test_container

    '''
    result = {}
    redconn = await hub.exec.utils.azurerm.get_client('redis', **kwargs)

    # Create a ExportRDBParameters object
    try:
        paramsmodel = await hub.exec.utils.azurerm.create_object_model(
            'redis',
            'ExportRDBParameters',
            prefix=prefix,
            container=container,
            format=format
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        cache = redconn.redis.export_data(
            name=name,
            resource_group_name=resource_group,
            parameters=paramsmodel
        )

        result = cache.result().as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('redis', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def force_reboot(hub, name, resource_group, reboot_type, shard_id, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Reboot specified Redis node(s). This operation requires write permission to the cache resource.
        There can be potential data loss.

    :param name: The name of the redis cache.

    :param resource_group: The name of the resource group.

    :param reboot_type: Which Redis node(s) to reboot. Depending on this value data loss is possible. Possible
        values include: 'PrimaryNode', 'SecondaryNode', 'AllNodes'.

    :param shard_id: If clustering is enabled, the ID of the shard to be rebooted.

    CLI Example:

    .. code-block:: bash

        azurerm.redis.force_reboot test_name test_rg test_type test_id

    '''
    result = {}
    redconn = await hub.exec.utils.azurerm.get_client('redis', **kwargs)

    try:
        cache = redconn.redis.force_reboot(
            name=name,
            resource_group_name=resource_group,
            reboot_type=reboot_type,
            shard_id=shard_id
        )

        result = cache.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('redis', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
