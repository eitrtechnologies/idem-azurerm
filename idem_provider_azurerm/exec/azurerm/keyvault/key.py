# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Key Vault Execution Module

.. versionadded:: VERSION

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
import datetime
import logging
import os

# Azure libs
HAS_LIBS = False
try:
    from azure.keyvault.keys._shared._generated.v7_0.models._models_py3 import KeyVaultErrorException
    from azure.keyvault.keys import KeyClient
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def get_key_client(hub, vault_url, **kwargs):
    '''
    .. versionadded:: VERSION

    Load the key client and return a KeyClient object.

    :param vault_url: The URL of the vault that the client will access.
    '''
    credential = await hub.exec.utils.azurerm.get_identity_credentials(**kwargs)

    key_client = KeyClient(vault_url=vault_url, credential=credential)

    return key_client


def _key_as_dict(key):
    result = {}
    attrs = [
        'id',
        'key_operations',
        'key_type',
        'name',
        'properties'
    ]
    for attr in attrs:
        val = getattr(key, attr)
        if attr == 'properties':
            val = _key_properties_as_dict(val)
        result[attr] = val
    return result


def _key_properties_as_dict(key_properties):
    result = {}
    props = [
        'created_on',
        'enabled',
        'expires_on',
        'id',
        'managed',
        'name',
        'not_before',
        'recovery_level',
        'tags',
        'updated_on',
        'vault_url',
        'version'
    ]
    for prop in props:
        val = getattr(key_properties, prop)
        if isinstance(val, datetime.datetime):
            val = val.isoformat()
        result[prop] = val
    return result


async def backup_key(hub, name, vault_url, **kwargs):
    '''
    .. versionadded:: VERSION

    Back up a key in a protected form useable only by Azure Key Vault. Requires key/backup permission. This is intended
        to allow copying a key from one vault to another. Both vaults must be owned by the same Azure subscription.
        Also, backup / restore cannot be performed across geopolitical boundaries. For example, a backup from a vault
        in a USA region cannot be restored to a vault in an EU region.

    :param name: The name of the key to back up.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.backup_key test_name test_vault

    '''
    '''
    result = {}
    kconn = await _get_key_client(vault_url, **kwargs)

    try:
        key = kconn.keys.backup_key(
            name=name,
        )

        result = key
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('key', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
    '''
    pass


async def create_ec_key(hub, name, vault_url, **kwargs):
    '''
    .. versionadded:: VERSION

    Create a new elliptic curve key or, if name is already in use, create a new version of the key. Requires the
        keys/create permission.

    :param name: The name of the new key.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.create_ec_key test_name test_vault

    '''
    result = {}
    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(hub, vault_url, **kwargs)

    try:
        key = kconn.create_ec_key(
            name=name,
        )

        result = _key_as_dict(key)

        log.debug('Key return: %s', result)
    except KeyVaultErrorException as exc:
        await hub.exec.utils.azurerm.log_cloud_error('key', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def list_(hub, vault_url, **kwargs):
    '''
    .. versionadded:: VERSION

    List identifiers and properties of all keys in the vault. Requires keys/list permission.

    :param vault_url: The URL of the vault that the client will access.

    CLI Example:

    .. code-block:: bash

        azurerm.keyvault.key.list test_vault

    '''
    result = {}

    kconn = await hub.exec.azurerm.keyvault.key.get_key_client(hub, vault_url, **kwargs)

    try:
        keys = kconn.list_properties_of_keys()

        for key in keys:
            result[key.name] = _key_properties_as_dict(key)

        log.debug('Key listing: %s', result)
    except KeyVaultErrorException as exc:
        await hub.exec.utils.azurerm.log_cloud_error('key', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
