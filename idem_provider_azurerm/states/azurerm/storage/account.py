# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Storage Account State Module

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

:configuration: This module requires Azure Resource Manager credentials to be passed as a dictionary of
    keyword arguments to the ``connection_auth`` parameter in order to work properly. Since the authentication
    parameters are sensitive, it's recommended to pass them to the states via pillar.

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

    Example Pillar for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass
            mysubscription:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD
'''

# Python libs
from __future__ import absolute_import
import logging
import re

try:
    from six.moves import range as six_range
except ImportError:
    six_range = range

log = logging.getLogger(__name__)

TREQ = {
    'present': {
        'require': [
            'azurerm.resource.group.present',
        ]
    }
}


async def present(hub, ctx, name, resource_group, sku, kind, location, identity=None, custom_domain=None, 
                  encryption=None, network_rule_set=None, access_tier=None, 
                  azure_files_identity_based_authentication=None, enable_https_traffic_only=None, is_hns_enabled=None, 
                  large_file_shares_state=None, routing_preference=None, tags=None, connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a storage account exists in the resource group.

    :param name: The name of the storage account.

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

    :param tags: A dictionary of strings can be passed as tag metadata to the storage account object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the 
        Azure Resource Manager API.

    NOTE: An access tier is required for when the kind is set to 'BlobStorage'. The access tier is used for billing.
        Possible values include: 'Hot' and 'Cool'.

    Example usage:

    .. code-block:: yaml

        Ensure storage account exists:
            azurerm.storage.account.present:
                - name: my_account
                - resource_group: my_rg
                - sku:
                    name: 'Standard_LRS'
                    tier: 'Standard'
                - kind: 'Storage'
                - location: 'eastus'
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

    '''
    ret = {
        'name': name,
        'result': False,
        'comment': '',
        'changes': {}
    }

    if not isinstance(connection_auth, dict):
        ret['comment'] = 'Connection information must be specified via connection_auth dictionary!'
        return ret

    account = await hub.exec.azurerm.storage.account.get_properties(
        name,
        resource_group,
        **connection_auth
    )

    if 'error' not in account:
        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(account.get('tags', {}), tags or {})
        if tag_changes:
            ret['changes']['tags'] = tag_changes

        sku_changes = await hub.exec.utils.dictdiffer.deep_diff(account.get('sku', {}), sku)
        if sku_changes:
            ret['changes']['sku'] = sku_changes
 
        encryption_changes = await hub.exec.utils.dictdiffer.deep_diff(account.get('encryption', {}), encryption or {})
        if encryption_changes:
            ret['changes']['encryption'] = encryption_changes
       
        domain_changes = await hub.exec.utils.dictdiffer.deep_diff(account.get('custom_domain', {}), 
                                                                                custom_domain or {})
        if domain_changes:
            ret['changes']['custom_domain'] = domain_changes

        if access_tier and access_tier != account.get('access_tier'):
            ret['changes']['access_tier'] = {
                'old': account.get('access_tier'),
                'new': access_tier
            }

        if not ret['changes']:
            ret['result'] = True
            ret['comment'] = 'Storage account {0} is already present.'.format(name)
            return ret

        if ctx['test']:
            ret['result'] = None
            ret['comment'] = 'Storage account {0} would be updated.'.format(name)
            return ret

    else:
        ret['changes'] = {
            'old': {},
            'new': {
                'name': name,
                'resource_group': resource_group,
                'sku': sku,
                'kind': kind,
                'location': location,
            }
        }

        if tags:
            ret['changes']['new']['tags'] = tags
        if access_tier:
            ret['changes']['new']['access_tier'] = access_tier
        if identity:
            ret['changes']['new']['identity'] = identity
        if custom_domain:
            ret['changes']['new']['custom_domain'] = custom_domain
        if encryption:
            ret['changes']['new']['encryption'] = encryption
        if network_rule_set:
            ret['changes']['new']['network_rule_set'] = network_rule_set
        if azure_files_identity_based_authentication:
            ret['changes']['new']['azure_files_identity_based_authentication'] = azure_files_identity_based_authentication
        if enable_https_traffic_only is not None:
            ret['changes']['new']['enable_https_traffic_only'] = enable_https_traffic_only
        if is_hns_enabled is not None:
            ret['changes']['new']['is_hns_enabled'] = is_hns_enabled
        if large_file_shares_state:
            ret['changes']['new']['large_file_shares_state'] = large_file_shares_state
        if routing_preference:
            ret['changes']['new']['routing_preference'] = routing_preference

    if ctx['test']:
        ret['comment'] = 'Storage account {0} would be created.'.format(name)
        ret['result'] = None
        return ret

    account_kwargs = kwargs.copy()
    account_kwargs.update(connection_auth)

    account = await hub.exec.azurerm.storage.account.create(
        name=name,
        resource_group=resource_group,
        tags=tags,
        sku=sku,
        kind=kind,
        location=location,
        identity=identity,
        custom_domain=custom_domain,
        encryption=encryption,
        network_rule_set=network_rule_set,
        access_tier=access_tier,
        enable_https_traffic_only=enable_https_traffic_only,
        is_hns_enabled=is_hns_enabled,
        large_file_shares_state=large_file_shares_state,
        routing_preference=routing_preference,
        **account_kwargs
    )

    if 'error' not in account:
        ret['result'] = True
        ret['comment'] = 'Storage account {0} has been created.'.format(name)
        return ret

    ret['comment'] = 'Failed to create storage acccount {0}! ({1})'.format(name, account.get('error'))
    if ret['result'] == False:
        ret['changes'] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None):
    '''
    .. versionadded:: 1.0.0

    Ensure a storage account does not exist in the resource group.

    :param name: The name of the storage account being deleted.

    :param resource_group: The name of the resource group that the storage account belongs to.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml
        Ensure storage account exists:
            azurerm.storage.account.absent:
                - name: my_account
                - resource_group: my_rg
                - connection_auth: {{ profile }}

    '''
    ret = {
        'name': name,
        'result': False,
        'comment': '',
        'changes': {}
    }

    if not isinstance(connection_auth, dict):
        ret['comment'] = 'Connection information must be specified via connection_auth dictionary!'
        return ret

    account = await hub.exec.azurerm.storage.account.get_properties(
        name,
        resource_group,
        **connection_auth
    )

    if 'error' in account:
        ret['result'] = True
        ret['comment'] = 'Storage account {0} was not found.'.format(name)
        return ret

    elif ctx['test']:
        ret['comment'] = 'Storage account {0} would be deleted.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': account,
            'new': {},
        }
        return ret

    deleted = await hub.exec.azurerm.storage.account.delete(name, resource_group, **connection_auth)

    if deleted:
        ret['result'] = True
        ret['comment'] = 'Storage account {0} has been deleted.'.format(name)
        ret['changes'] = {
            'old': account,
            'new': {}
        }
        return ret

    ret['comment'] = 'Failed to delete storage account {0}!'.format(name)
    return ret
