# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Key Vault State Module

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
from operator import itemgetter

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


async def present(hub, ctx, name, resource_group, location, tenant_id, sku, access_policies=None, vault_uri=None,
                  create_mode=None, enable_soft_delete=None, enable_purge_protection=None, enabled_for_deployment=None,
                  enabled_for_disk_encryption=None, enabled_for_template_deployment=None, tags=None,
                  connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a specified keyvault exists.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the vault belongs.

    FILL IN THE REST OF THE PARAMS ONCE THE CREATE_OR_UPDATE EXEC MODULE IS DONE AND TESTED

    :param tags: A dictionary of strings can be passed as tag metadata to the key vault.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key vault exists:
            azurerm.key_vault.vault.present:
                - name: my_vault
                - resource_group: my_rg
                - location: my_location
                - tenant_id: my_tenant
                - sku: my_sku
                - access_policies:
                  - tenant_id: my_tenant
                    object_id: my_object
                    permissions:
                      keys:
                        - perm1
                        - perm2
                        - perm3
                      secrets:
                        - perm1
                        - perm2
                        - perm3
                      certificates:
                        - perm1
                        - perm2
                        - perm3
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

    vault = await hub.exec.azurerm.key_vault.vault.get(
        name,
        resource_group,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' not in vault:
        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(vault.get('tags', {}), tags or {})
        if tag_changes:
            ret['changes']['tags'] = tag_changes
    
        # Checks for changes in the account_policies parameter
        if len(access_policies) == len(vault.get('properties').get('access_policies', [])):
            new_policies_sorted = sorted(access_policies, key=itemgetter('object_id'))
            old_policies_sorted = sorted(vault.get('properties').get('access_policies', []), key=itemgetter('object_id'))
            index = 0
            for policy in new_policies_sorted:
                changes = await hub.exec.utils.dictdiffer.deep_diff(vault.get('properties').get('access_policies')[index], policy)
                index = index + 1
                if changes:
                    ret['changes']['access_policies'] = {
                        'old': vault.get('properties').get('access_policies', []),
                        'new': access_policies
                    }
                    break
        else:
            ret['changes']['access_policies'] = {
                'old': vault.get('properties').get('access_policies', []),
                'new': access_policies
            }

        if sku != vault.get('properties').get('sku').get('name'):
            ret['changes']['sku'] = {
                'old': vault.get('properties').get('sku').get('name'),
                'new': sku
            } 

        if enabled_for_deployment is not None:
            if enabled_for_deployment != vault.get('properties').get('enabled_for_deployment'):
                ret['changes']['enabled_for_deployment'] = {
                    'old': vault.get('properties').get('enabled_for_deployment'),
                    'new': enabled_for_deployment
                }

        if enabled_for_disk_encryption is not None:
            if enabled_for_disk_encryption != vault.get('properties').get('enabled_for_disk_encryption'):
                ret['changes']['enabled_for_disk_encryption'] = {
                    'old': vault.get('properties').get('enabled_for_disk_encryption'),
                    'new': enabled_for_disk_encryption
                }

        if enabled_for_template_deployment is not None:
            if enabled_for_template_deployment != vault.get('properties').get('enabled_for_template_deployment'):
                ret['changes']['enabled_for_template_deployment'] = {
                    'old': vault.get('properties').get('enabled_for_template_deployment'),
                    'new': enabled_for_template_deployment
                }

        if enable_soft_delete is not None:
            if enable_soft_delete != vault.get('properties').get('enable_soft_delete'):
                ret['changes']['enable_soft_delete'] = {
                    'old': vault.get('properties').get('enable_soft_delete'),
                    'new': enable_soft_delete
                }

        if enable_purge_protection is not None:
            if enable_purge_protection != vault.get('properties').get('enable_purge_protection'):
                ret['changes']['enable_purge_protection'] = {
                    'old': vault.get('properties').get('enable_purge_protection'),
                    'new': enable_purge_protection
                }

        if not ret['changes']:
            ret['result'] = True
            ret['comment'] = 'Key Vault {0} is already present.'.format(name)
            return ret

        if ctx['test']:
            ret['result'] = None
            ret['comment'] = 'Key Vault {0} would be updated.'.format(name)
            return ret

    else:
        ret['changes'] = {
            'old': {},
            'new': {
                'name': name,
                'resource_group': resource_group,
                'location': location,
                'tenant_id': tenant_id,
                'sku': sku
            }
        }

        if tags:
            ret['changes']['new']['tags'] = tags
        if access_policies:
            ret['changes']['new']['access_policies'] = access_policies
        if vault_uri:
            ret['changes']['new']['vault_uri'] = vault_uri
        if enabled_for_deployment is not None:
            ret['changes']['new']['enabled_for_deployment'] = enabled_for_deployment
        if enabled_for_disk_encryption is not None:
            ret['changes']['new']['enabled_for_disk_encryption'] = enabled_for_disk_encryption
        if enabled_for_template_deployment is not None:
            ret['changes']['new']['enabled_for_template_deployment'] = enabled_for_template_deployment
        if enable_soft_delete is not None:
            ret['changes']['new']['enable_soft_delete'] = enable_soft_delete 
        if create_mode:
            ret['changes']['new']['create_mode'] = create_mode
        if enable_purge_protection:
            ret['changes']['new']['enable_purge_protection'] = enable_purge_protection

    if ctx['test']:
        ret['comment'] = 'Key vault {0} would be created.'.format(name)
        ret['result'] = None
        return ret

    vault_kwargs = kwargs.copy()
    vault_kwargs.update(connection_auth)

    vault = await hub.exec.azurerm.key_vault.vault.create_or_update(
        name=name,
        resource_group=resource_group,
        location=location,
        tenant_id=tenant_id,
        sku=sku,
        access_policies=access_policies,
        vault_uri=vault_uri,
        create_mode=create_mode,
        enable_soft_delete=enable_soft_delete,
        enable_purge_protection=enable_purge_protection,
        enabled_for_deployment=enabled_for_deployment,
        enabled_for_disk_encryption=enabled_for_disk_encryption,
        enabled_for_template_deployment=enabled_for_template_deployment,
        tags=tags,
        **vault_kwargs
    )

    if 'error' not in vault:
        ret['result'] = True
        ret['comment'] = 'Key Vault {0} has been created.'.format(name)
        return ret

    ret['comment'] = 'Failed to create Key Vault {0}! ({1})'.format(name, vault.get('error'))
    if ret['result'] == False:
        ret['changes'] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None):
    '''
    .. versionadded:: 1.0.0

    Ensure a specified key vault does not exist.

    :param name: The name of the vault.

    :param resource_group: The name of the resource group to which the vault belongs.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure key vault is absent:
            azurerm.key_vault.vault.absent:
                - name: my_vault
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

    vault = await hub.exec.azurerm.key_vault.vault.get(
        name,
        resource_group,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' in vault:
        ret['result'] = True
        ret['comment'] = 'Key Vault {0} was not found.'.format(name)
        return ret

    elif ctx['test']:
        ret['comment'] = 'Key Vault {0} would be deleted.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': vault,
            'new': {},
        }
        return ret

    deleted = await hub.exec.azurerm.key_vault.vault.delete(
        name,
        resource_group,
        **connection_auth
    )

    if deleted:
        ret['result'] = True
        ret['comment'] = 'Key Vault {0} has been deleted.'.format(name)
        ret['changes'] = {
            'old': vault,
            'new': {}
        }
        return ret

    ret['comment'] = 'Failed to delete Key Vault {0}!'.format(name)
    return ret
