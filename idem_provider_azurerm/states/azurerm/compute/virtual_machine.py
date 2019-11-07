# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Compute Virtual Machine State Module

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

    Example states using Azure Resource Manager authentication:

    .. code-block:: jinja

        Ensure virtual machine exists:
          azurerm.compute.virtual_machine.present:
            - name: idem-vm01
            - resource_group: idem
            - vm_size: Standard_B1s
            - virtual_network: vnet1
            - subnet: default
            - allocate_public_ip: True
            - ssh_public_keys:
                - /home/myuser/.ssh/id_rsa.pub
            - tags:
                contact_name: Elmer Fudd Gantry
            - connection_auth: {{ profile }}

        Ensure virtual machine is absent:
            azurerm.compute.virtual_machine.absent:
                - name: idem-vm01
                - resource_group: idem
                - connection_auth: {{ profile }}

'''

# Python libs
from __future__ import absolute_import
import logging

log = logging.getLogger(__name__)


async def present(hub, ctx, name, resource_group, tags=None, connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a virtual machine exists.

    :param name:
        Name of the virtual machine.

    :param resource_group:
        The resource group assigned to the virtual machine.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the virtual machine object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual machine exists:
            azurerm.compute.virtual_machine.present:
                - name: idem-vm01
                - resource_group: idem
                - vm_size: Standard_B1s
                - virtual_network: vnet1
                - subnet: default
                - allocate_public_ip: True
                - ssh_public_keys:
                    - /home/myuser/.ssh/id_rsa.pub
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

    vm = await hub.exec.azurerm.compute.virtual_machine.get(
        name,
        resource_group,
        azurearm_log_level='info',
        **connection_auth
    )

    new_vm = True

    if 'error' not in vm:
        new_vm = False

        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(vm.get('tags', {}), tags or {})

        if tag_changes:
            ret['changes']['tags'] = tag_changes

        if not ret['changes']:
            ret['result'] = True
            ret['comment'] = 'Virtual machine {0} is already present.'.format(name)
            return ret

        if ctx['test']:
            ret['result'] = None
            ret['comment'] = 'Virtual machine {0} would be updated.'.format(name)
            return ret

    if ctx['test']:
        ret['comment'] = 'Virtual machine {0} would be created.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': {},
            'new': {
                'name': name,
                'tags': tags,
                **kwargs
            }
        }
        return ret

    vm_kwargs = kwargs.copy()
    vm_kwargs.update(connection_auth)

    vm = await hub.exec.azurerm.compute.virtual_machine.create_or_update(
        name=name,
        resource_group=resource_group,
        tags=tags,
        **vm_kwargs
    )

    if new_vm:
        ret['changes'] = {
            'old': {},
            'new': vm
        }

    if 'error' not in vm:
        ret['result'] = True
        ret['comment'] = 'Virtual machine {0} has been created.'.format(name)
        return ret

    ret['comment'] = 'Failed to create virtual machine {0}! ({1})'.format(name, vm.get('error'))
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a virtual machine does not exist in a resource group.

    :param name:
        Name of the virtual machine.

    :param resource_group:
        Name of the resource group containing the virtual machine.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.
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

    vm = await hub.exec.azurerm.compute.virtual_machine.get(
        name,
        resource_group,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' in vm:
        ret['result'] = True
        ret['comment'] = 'Virtual machine {0} was not found.'.format(name)
        return ret

    elif ctx['test']:
        ret['comment'] = 'Virtual machine {0} would be deleted.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': vm,
            'new': {},
        }
        return ret

    vm_kwargs = kwargs.copy()
    vm_kwargs.update(connection_auth)

    deleted = await hub.exec.azurerm.compute.virtual_machine.delete(name, resource_group, **vm_kwargs)

    if deleted:
        ret['result'] = True
        ret['comment'] = 'Virtual machine {0} has been deleted.'.format(name)
        ret['changes'] = {
            'old': vm,
            'new': {}
        }
        return ret

    ret['comment'] = 'Failed to delete virtual machine {0}!'.format(name)
    return ret
