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


async def present(hub, ctx, name, address_prefixes, resource_group, dns_servers=None, tags=None, connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a virtual network exists.

    :param name:
        Name of the virtual network.

    :param resource_group:
        The resource group assigned to the virtual network.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the virtual network object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure storage account exists:
            azurerm.storage.account.present:
                - name: my_account
                - resource_group: my_rg
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
    pass


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
