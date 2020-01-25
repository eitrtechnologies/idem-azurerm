# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Storage Account Operations Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 4.0.0
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
    import azure.mgmt.storage  # pylint: disable=unused-import
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def check_name_availability(hub, name, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Checks that the storage account name is valid and is not already in use.

    :param name: The name of the storage account.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.check_name_availability test_name

    '''
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        status = storconn.storage_accounts.check_name_availability(
            name=name
        )

        result = status.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def create(hub, name, resource_group, sku, kind, location, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Asynchronously creates a new storage account with the specified parameters. If an account is already created and a
        subsequent create request is issued with different properties, the account properties will be updated. If an
        account is already created and a subsequent create or update request is issued with the exact same set of
        properties, the request will succeed.

    :param name: The name of the storage account being created. Storage account names must be between 3 and 24
        characters in length and use numbers and lower-case letters only.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param sku: A dictionary representing a storage account SKU. Valid parameters are:
          - ``name``: The name of the storage account SKU. This is required. Possible values include: 'Standard_LRS',
                      'Standard_GRS', 'Standard_RAGRS', 'Standard_ZRS', 'Premium_LRS', 'Premium_ZRS', 'Standard_GZRS',
                      'Standard_RAGZRS'.
          - ``tier``: The tier of the storage account SKU. Possible values include: 'Standard', 'Premium'.

    :param kind: Indicates the type of storage account. Possible values include: 'Storage', 'StorageV2', 'BlobStorage'.

    :param location: Gets or sets the location of the resource. This will be one of the supported and registered Azure
        Geo Regions (e.g. West US, East US, Southeast Asia, etc.). The geo region of a resource cannot be changed once
        it is created, but if an identical geo region is specified on update, the request will succeed.

    NOTE: An access tier is required for when the kind is set to 'BlobStorage'. The access tier is used for billing. 
        Possible values include: 'Hot' and 'Cool'.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.create test_name test_group test_sku test_kind test_location

    '''
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        accountmodel = await hub.exec.utils.azurerm.create_object_model(
            'storage',
            'StorageAccountCreateParameters',
            sku=sku,
            kind=kind,
            location=location,   
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        account = storconn.storage_accounts.create(
            account_name=name,
            resource_group_name=resource_group,
            parameters=accountmodel
        )

        result = account.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def delete(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Delete a storage account.

    :param name: The name of the storage account being deleted.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.delete test_name test_group

    '''
    result = False
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        account = storconn.storage_accounts.delete(
            account_name=name,
            resource_group_name=resource_group
        )
        
        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)

    return result


async def get_properties(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Returns the properties for the specified storage account including but not limited to name, SKU name, location,
        and account status. The ListKeys operation should be used to retrieve storage keys.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.get_properties test_name test_group

    '''
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        props = storconn.storage_accounts.get_properties(
            account_name=name,
            resource_group_name=resource_group
        )

        result = props.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_(hub, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Lists all the storage accounts available under the subscription. Note that storage keys are not returned; use the
        ListKeys operation for this.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list

    '''
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        accounts = await hub.exec.utils.azurerm.paged_object_to_list(
            storconn.storage_accounts.list()
        )

        for account in accounts:
            result[account['name']] = account
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_account_sas(hub, name, resource_group, services, resource_types, permissions, shared_access_expiry_time,
                           **kwargs):
    '''
    .. versionadded:: 1.0.0

    List SAS credentials of a storage account.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param services: The signed services accessible with the account SAS. Possible values include: Blob (b), Queue (q), 
        Table (t), File (f). Possible values include: 'b', 'q', 't', 'f'.

    :param resource_types: The signed resource types that are accessible with the account SAS. Service (s): Access to
        service-level APIs; Container (c): Access to container-level APIs; Object (o): Access to object-level APIs for
        blobs, queue messages, table entities, and files. Possible values include: 's', 'c', 'o'.

    :param permissions: The signed permissions for the account SAS. Possible values include: Read (r), Write (w), Delete
        (d), List (l), Add (a), Create (c), Update (u) and Process (p). Possible values include: 'r', 'd', 'w', 'l', 
        'a', 'c', 'u', 'p'.

    :param shared_access_expiry_time: The time at which the shared access signature becomes invalid.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_account_sas test_name test_group test_services test_types test_perms test_time

    '''
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        accountmodel = await hub.exec.utils.azurerm.create_object_model(
            'storage',
            'AccountSasParameters',
            permissions=permissions,
            shared_access_expiry_time=shared_access_expiry_time,
            resource_types=resource_types,
            services=services,
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        creds = await hub.exec.utils.azurerm.paged_object_to_list(
            storconn.storage_accounts.list_account_sas(
                account_name=name,
                resource_group_name=name,
                parameters=accountmodel
            )
        )

        result = creds.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_by_resource_group(hub, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Lists all the storage accounts available under the given resource group. Note that storage keys are not returned; 
        use the ListKeys operation for this.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_by_resource_group test_group

    '''
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)
    try:
        accounts = await hub.exec.utils.azurerm.paged_object_to_list(
            storconn.storage_accounts.list_by_resource_group(
                resource_group_name=resource_group
            )
        )

        for account in accounts:
            result[account['name']] = account
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_keys(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Lists the access keys or Kerberos keys (if active directory enabled) for the specified storage account.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_keys test_name test_group

    '''
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)
    try:
        keys = storconn.storage_accounts.list_keys(
            account_name=name,
            resource_group_name=resource_group
        )

        result = keys.as_dict() 
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_service_sas(hub, name, resource_group, canonicalized_resource, **kwargs):
    '''
    .. versionadded:: 1.0.0

    List service SAS credentials of a specific resource.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param canonicalized_resource: The canonical path to the signed resource.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.list_service_sas test_name test_group test_resource

    '''
    result = {}
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        accountmodel = await hub.exec.utils.azurerm.create_object_model(
            'storage',
            'ServiceSasParameters',
            canonicalized_resource=canonicalized_resource,
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        creds = await hub.exec.utils.azurerm.paged_object_to_list(
            storconn.storage_accounts.list_account_sas(
                account_name=name,
                resource_group_name=name,
                parameters=accountmodel
            )
        )

        result = creds.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def regenerate_key(hub, name, resource_group, key_name, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Regenerates one of the access keys or Kerberos keys for the specified storage account.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param key_name: The name of storage keys that want to be regenerated. Possible values are key1, key2, kerb1, kerb2.

    CLI Example:

    .. code-block:: bash

        azurerm.storage.account.renegerate_key test_name test_group test_key

    '''
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        keys = storconn.storage_accounts.regenerate_key(
            resource_group_name=resource_group,
            account_name=name,
            key_name=key_name,
            **kwargs
        )

        result = keys
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def update(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    The update operation can be used to update the SKU, encryption, access tier, or tags for a storage account. It can 
        also be used to map the account to a custom domain. Only one custom domain is supported per storage account; 
        the replacement/change of custom domain is not supported. In order to replace an old custom domain, the old 
        value must be cleared/unregistered before a new value can be set. The update of multiple properties is 
        supported. This call does not change the storage keys for the account. If you want to change the storage 
        account keys, use the regenerate keys operation. The location and name of the storage account cannot be changed
        after creation.

    :param name: The name of the storage account.

    :param resource_group: The name of the resource group that the storage account belongs to.

    CLI Example:

    .. code-block:: bash                                  
                                                                
        azurerm.storage.account.update test_name test_group

    '''
    storconn = await hub.exec.utils.azurerm.get_client('storage', **kwargs)

    try:
        accountmodel = await hub.exec.utils.azurerm.create_object_model(
            'storage',
            'StorageAccountUpdateParameters',
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        account = storconn.storage_accounts.update(
            account_name=name,
            resource_group_name=resource_group,
            parameters=accountmodel
        )

        result = account.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('storage', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result
