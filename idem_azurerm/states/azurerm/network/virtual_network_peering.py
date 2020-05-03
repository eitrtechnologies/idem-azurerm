# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Virtual Network Peering State Module

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

        Ensure virtual network exists:
            azurerm.network.virtual_network.present:
                - name: my_vnet
                - resource_group: my_rg
                - address_prefixes:
                    - '10.0.0.0/8'
                    - '192.168.0.0/16'
                - dns_servers:
                    - '8.8.8.8'
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure virtual network is absent:
            azurerm.network.virtual_network.absent:
                - name: other_vnet
                - resource_group: my_rg
                - connection_auth: {{ profile }}

'''
# Python libs
from __future__ import absolute_import
import logging
import re

log = logging.getLogger(__name__)

TREQ = {
    'present': {
        'require': [
            'states.azurerm.resource.group.present',
            'states.azurerm.network.virtual_network.present',
        ]
    },
}


async def present(hub, ctx, name, remote_virtual_network, virtual_network, resource_group, remote_vnet_group=None,
            allow_virtual_network_access=True, allow_forwarded_traffic=False, allow_gateway_transit=False,
            use_remote_gateways=False, connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a virtual network peering object exists.

    :param name:
        Name of the peering object.

    :param remote_virtual_network:
        The name of the remote virtual network.

    :param remote_vnet_group:
        The resource group of the remote virtual network. Defaults to the same resource group
        as the local virtual network.

    :param virtual_network:
        Name of the existing virtual network to contain the peering object.

    :param resource_group:
        The resource group assigned to the local virtual network.

    :param allow_virtual_network_access:
        Whether the VMs in the local virtual network space would be able to access
        the VMs in remote virtual network space.

    :param allow_forwarded_traffic:
        Whether the forwarded traffic from the VMs in the local virtual network will
        be allowed/disallowed in remote virtual network.

    :param allow_gateway_transit:
        If gateway links can be used in remote virtual networking to link to this virtual network.

    :param use_remote_gateways:
        If remote gateways can be used on this virtual network. If the flag is set to true, and allow_gateway_transit
        on remote peering is also true, virtual network will use gateways of remote virtual network for transit.
        Only one peering can have this flag set to true. This flag cannot be set if virtual network already has a
        gateway.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure virtual network peering exists:
            azurerm.network.virtual_network_peering.present:
                - name: vnet1_to_vnet2
                - virtual_network: vnet1
                - resource_group: group1
                - remote_virtual_network: vnet2
                - remote_vnet_group: group2
                - allow_virtual_network_access: True
                - allow_forwarded_traffic: False
                - allow_gateway_transit: False
                - use_remote_gateways: False
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

    peering = await hub.exec.azurerm.network.virtual_network_peering.get(
        name,
        virtual_network,
        resource_group,
        azurerm_log_level='info',
        **connection_auth
    )

    if 'error' not in peering:
        remote_vnet = None
        if peering.get('remote_virtual_network', {}).get('id'):
            remote_vnet = peering['remote_virtual_network']['id'].split('/')[-1]

        if remote_virtual_network != remote_vnet:
            ret['changes']['remote_virtual_network'] = {
                'old': remote_vnet,
                'new': remote_virtual_network
            }

        for bool_opt in ['use_remote_gateways', 'allow_forwarded_traffic', 'allow_virtual_network_access', 'allow_gateway_transit']:
            if locals()[bool_opt] != peering.get(bool_opt):
                ret['changes'][bool_opt] = {
                    'old': peering.get(bool_opt),
                    'new': locals()[bool_opt]
                }

        if not ret['changes']:
            ret['result'] = True
            ret['comment'] = 'Peering object {0} is already present.'.format(name)
            return ret

        if ctx['test']:
            ret['result'] = None
            ret['comment'] = 'Peering object {0} would be updated.'.format(name)
            return ret

    else:
        ret['changes'] = {
            'old': {},
            'new': {
                'name': name,
                'remote_virtual_network': remote_virtual_network,
                'remote_vnet_group': (remote_vnet_group or resource_group),
                'use_remote_gateways': use_remote_gateways,
                'allow_forwarded_traffic': allow_forwarded_traffic,
                'allow_virtual_network_access': allow_virtual_network_access,
                'allow_gateway_transit': allow_gateway_transit
            }
        }

    if ctx['test']:
        ret['comment'] = 'Subnet {0} would be created.'.format(name)
        ret['result'] = None
        return ret

    peering_kwargs = kwargs.copy()
    peering_kwargs.update(connection_auth)

    peering = await hub.exec.azurerm.network.virtual_network_peering.create_or_update(
        name=name,
        remote_virtual_network=remote_virtual_network,
        remote_vnet_group=remote_vnet_group,
        virtual_network=virtual_network,
        resource_group=resource_group,
        use_remote_gateways=use_remote_gateways,
        allow_forwarded_traffic=allow_forwarded_traffic,
        allow_virtual_network_access=allow_virtual_network_access,
        allow_gateway_transit=allow_gateway_transit,
        **peering_kwargs
    )

    # This is a special case where one side of the peering has been deleted and recreated.
    # In order to establish the new peer, the remote peer needs to be set back to "Initiated" state.
    if peering.get('error', '').startswith('Azure Error: RemotePeeringIsDisconnected'):
        rname_match = re.search('because remote peering (\S+) referencing parent virtual network', peering['error'])
        remote_name = rname_match.group(1).split('/')[-1]

        remote_peering = await hub.exec.azurerm.network.virtual_network_peering.get(
            name=remote_name,
            virtual_network=remote_virtual_network,
            resource_group=remote_vnet_group,
            azurerm_log_level='info',
            **connection_auth
        )

        remote_peering_kwargs = remote_peering.copy()
        remote_peering_kwargs.update(connection_auth)
        remote_peering_kwargs['peering_state'] = 'Initiated'
        remote_peering_kwargs.pop('remote_virtual_network')

        remote_peering = await hub.exec.azurerm.network.virtual_network_peering.create_or_update(
            remote_virtual_network=virtual_network,
            remote_vnet_group=resource_group,
            virtual_network=remote_virtual_network,
            resource_group=remote_vnet_group,
            **remote_peering_kwargs
        )

        peering = await hub.exec.azurerm.network.virtual_network_peering.create_or_update(
            name=name,
            remote_virtual_network=remote_virtual_network,
            remote_vnet_group=remote_vnet_group,
            virtual_network=virtual_network,
            resource_group=resource_group,
            use_remote_gateways=use_remote_gateways,
            allow_forwarded_traffic=allow_forwarded_traffic,
            allow_virtual_network_access=allow_virtual_network_access,
            allow_gateway_transit=allow_gateway_transit,
            **peering_kwargs
        )

    if 'error' not in peering:
        ret['result'] = True
        ret['comment'] = 'Peering object {0} has been created.'.format(name)
        return ret

    ret['comment'] = 'Failed to create peering object {0}! ({1})'.format(name, peering.get('error'))
    if not ret['result']:
        ret['changes'] = {}
    return ret


async def absent(hub, ctx, name, virtual_network, resource_group, connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a virtual network peering object does not exist in the virtual network.

    :param name:
        Name of the peering object.

    :param virtual_network:
        Name of the existing virtual network containing the peering object.

    :param resource_group:
        The resource group assigned to the virtual network.

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

    peering = await hub.exec.azurerm.network.virtual_network_peering.get(
        name,
        virtual_network,
        resource_group,
        azurerm_log_level='info',
        **connection_auth
    )

    if 'error' in peering:
        ret['result'] = True
        ret['comment'] = 'Peering object {0} was not found.'.format(name)
        return ret

    elif ctx['test']:
        ret['comment'] = 'Peering object {0} would be deleted.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': peering,
            'new': {},
        }
        return ret

    deleted = await hub.exec.azurerm.network.virtual_network_peering.delete(
        name,
        virtual_network,
        resource_group,
        **connection_auth
    )

    if deleted:
        ret['result'] = True
        ret['comment'] = 'Peering object {0} has been deleted.'.format(name)
        ret['changes'] = {
            'old': peering,
            'new': {}
        }
        return ret

    ret['comment'] = 'Failed to delete peering object {0}!'.format(name)
    return ret
