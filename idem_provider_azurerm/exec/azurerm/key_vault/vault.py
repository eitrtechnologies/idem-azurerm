# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Key Vault Execution Module

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
    import azure.mgmt.keyvault.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)

async def check_name_availability(hub, name, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Checks that the vault name is valid and is not already in use.

    :param name: The vault name.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.check_name_availability test_name

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        avail = vconn.vaults.check_name_availability(
            name=name,
        )

        result = avail.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def create_or_update(hub, name, resource_group, PARAMETERS=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Create or update a key vault in the specified subscription.

    :param name: The vault name.

    :param resource_group: The name of the resource group to which the vault belongs.

    :param PARAMETERS: UPDATE

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.create_or_update test_name test_rg ...

    '''
    pass


async def delete(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Deletes the specified Azure key vault.                                                                                                                                         
    
    :param name: The vault name.

    :param resource_group: The name of the resource group to which the vault belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.delete test_name test_rg

    '''
    result = False
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vault = vconn.vaults.delete(
            vault_name=name,
            resource_group_name=resource_group
        )

        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)

    return result


async def get(hub, name, resource_group, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets the specified Azure key vault.

    :param name: The vault name.

    :param resource_group: The name of the resource group to which the vault belongs.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.get test_name test_rg

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vault = vconn.vaults.get(
            vault_name=name,
            resource_group_name=resource_group
        )

        result = vault.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def get_deleted(hub, name, location, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets the deleted Azure key vault.

    :param name: The vault name.

    :param location: The location of the deleted vault.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.get_deleted test_name test_location

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vault = vconn.vaults.get_deleted(
            vault_name=name,
            location=location
        )

        result = vault.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_(hub, top=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    The List operation gets information about the vaults associated with the subscription.

    :param top: Maximum number of results to return.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.list

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)
    
    try:
        vaults = await hub.exec.utils.azurerm.paged_object_to_list(
            vconn.vaults.list(
                top=top
            )
        )

        for vault in vaults:
            result[vault['name']] = vault
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_by_resource_group(hub, resource_group, top=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    The List operation gets information about the vaults associated with the subscription
        and within the specified resource group.

    :param resource_group: The name of the resource group to which the vault belongs.

    :param top: Maximum number of results to return.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.list_by_resource_group test_rg

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vaults = await hub.exec.utils.azurerm.paged_object_to_list(
            vconn.vaults.list_by_resource_group(
                resource_group_name=resource_group,
                top=top
            )
        )

        for vault in vaults:
            result[vault['name']] = vault
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_by_subscription(hub, top=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    The List operation gets information about the vaults associated with the subscription.

    :param top: Maximum number of results to return.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.list_by_subscription

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vaults = await hub.exec.utils.azurerm.paged_object_to_list(
            vconn.vaults.list_by_subscription(
                top=top
            )
        )

        for vault in vaults:
            result[vault['name']] = vault
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_deleted(hub, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets information about the deleted vaults in a subscription.
 
    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.list_deleted

    '''
    result = {}
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vaults = await hub.exec.utils.azurerm.paged_object_to_list(
            vconn.vaults.list_deleted()
        )

        for vault in vaults:
            result[vault['name']] = vault
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def purge_deleted(hub, name, location, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Permanently deletes (purges) the specified Azure key vault.

    :param name: The name of the soft-deleted vault.

    :param location: The location of the soft-deleted vault.

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.purge_deleted test_name test_location

    '''
    result = False
    vconn = await hub.exec.utils.azurerm.get_client('keyvault', **kwargs)

    try:
        vault = vconn.vaults.purge_deleted(
            vault_name=name,
            location=location
        )

        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('keyvault', str(exc), **kwargs)

    return result


async def update(hub, name, resource_group, PROPERTIES=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Update a key vault in the specified subscription.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the server belongs.

    :param PROPERTIES: UPDATE

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.update test_name test_rg ...

    '''
    pass


async def update_access_policy(hub, name, resource_group, operation_kind, PROPERTIES=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Update access policies in a key vault in the specified subscription.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the server belongs.

    :param operation_kind: Name of the operation. Possible values include: 'add', 'replace', and 'remove'

    :param PROPERTIES: UPDATE

    CLI Example:

    .. code-block:: bash

        azurerm.key_vault.vault.update test_name test_rg test_kind ...

    '''
    pass
