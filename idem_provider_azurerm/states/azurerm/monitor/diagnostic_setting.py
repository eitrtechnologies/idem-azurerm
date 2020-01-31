# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Diagnostic Setting State Module

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


async def present(hub, ctx, name, resource_uri, metrics, logs, workspace_id=None, storage_account_id=None,
                  service_bus_rule_id=None, event_hub_authorization_rule_id=None, event_hub_name=None, tags=None,
                  connection_auth=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a diagnostic setting exists. At least one destination for the diagnostic setting is required. The three
        possible destinations for the diagnostic settings are as follows:
            1. Archive the diagnostic settings to a stroage account. This would require the storage_account_id param.
            2. Stream the diagnostic settings to an event hub. This would require the event_hub_name and
               event_hub_authorization_rule_id params.
            3. Send the diagnostic settings to Log Analytics. This would require the workspace_id param.
        Any combination of these destinations is acceptable.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    :param metrics: The list of metric settings. This is a list of dictionaries representing MetricSettings objects.

    :param logs: The list of logs settings. This is a list of dictionaries representing LogSettings objects.

    :param workspace_id: The workspace ID (resource ID of a Log Analytics workspace) for a Log Analytics workspace to
        which you would like to send Diagnostic Logs.

    :param storage_account_id: The resource ID of the storage account to which you would like to send Diagnostic Logs.

    :param service_bus_rule_id: The service bus rule ID of the diagnostic setting.
        This is here to maintain backwards compatibility.

    :param event_hub_authorization_rule_id: The resource ID for the event hub authorization rule.

    :param event_hub_name: The name of the event hub. If none is specified, the default event hub will be selected.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the diagnostic settings object.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure diagnostic setting exists:
            azurerm.monitor.diagnostic_setting.present:
                - name: my_setting
                - resource_uri: my_resource
                - metrics: [{'category': 'AllMetrics', 'enabled': True, 'retention_policy': {'enabled': False, 'days': 0}}]
                - logs: [{'category': 'VMProtectionAlerts', 'enabled': False, 'retention_policy': {'enabled': False, 'days': 0}}]}
                - storage_account_id: my_account_id
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

    setting = await hub.exec.azurerm.monitor.diagnostic_setting.get(
        name,
        resource_uri,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' not in setting:
        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(setting.get('tags', {}), tags or {})
        if tag_changes:
            ret['changes']['tags'] = tag_changes
    
        # Metrics and logs need to be compared here

        if storage_account_id:
            if storage_account_id != setting.get('storage_account_id', None):
                ret['changes']['storage_account_id'] = {
                    'old': setting.get('storage_account_id'),
                    'new': storage_account_id
                }

        if workspace_id:
            if workspace_id != setting.get('workspace_id', None):
                ret['changes']['workspace_id'] = {
                    'old': setting.get('workspace_id'),
                    'new': workspace_id
                }

        if service_bus_rule_id:
            if service_bus_rule_id != setting.get('service_bus_rule_id', None):
                ret['changes']['service_bus_rule_id'] = {
                    'old': setting.get('service_bus_rule_id'),
                    'new': service_bus_rule_id
                }

        if event_hub_authorization_rule_id:
            if event_hub_authorization_rule_id != setting.get('event_hub_authorization_rule_id', None):
                ret['changes']['event_hub_authorization_rule_id'] = {
                    'old': setting.get('event_hub_authorization_rule_id'),
                    'new': event_hub_authorization_rule_id
                }

        if event_hub_name:
            if event_hub_name != setting.get('event_hub_name', None):
                ret['changes']['event_hub_name'] = {
                    'old': setting.get('event_hub_name'),
                    'new': event_hub_name
                }

        if not ret['changes']:
            ret['result'] = True
            ret['comment'] = 'Diagnostic setting {0} is already present.'.format(name)
            return ret

        if ctx['test']:
            ret['result'] = None
            ret['comment'] = 'Diagnostic setting {0} would be updated.'.format(name)
            return ret

    else:
        ret['changes'] = {
            'old': {},
            'new': {
                'name': name,
                'resource_uri': resource_uri,
                'metrics': metrics,
                'logs': logs,
            }
        }

        if tags:
            ret['changes']['new']['tags'] = tags
        if storage_account_id:
            ret['changes']['new']['storage_account_id'] = storage_account_id
        if workspace_id:
            ret['changes']['new']['workspace_id'] = workspace_id
        if service_bus_rule_id:
            ret['changes']['new']['service_bus_rule_id'] = service_bus_rule_id
        if event_hub_authorization_rule_id:
            ret['changes']['new']['event_hub_authorization_rule_id'] = event_hub_authorization_rule_id
        if event_hub_name:
            ret['changes']['new']['event_hub_name'] = event_hub_name

    if ctx['test']:
        ret['comment'] = 'Diagnostic setting {0} would be created.'.format(name)
        ret['result'] = None
        return ret

    setting_kwargs = kwargs.copy()
    setting_kwargs.update(connection_auth)

    setting = await hub.exec.azurerm.monitor.diagnostic_setting.create_or_update(
        name=name,
        resource_uri=resource_uri,
        logs=logs,
        metrics=metrics,
        storage_account_id=storage_account_id,
        workspace_id=workspace_id,
        event_hub_name=event_hub_name,
        event_hub_authorization_rule_id=event_hub_authorization_rule_id,
        service_bus_rule_id=service_bus_rule_id,
        tags=tags,
        **setting_kwargs
    )

    if 'error' not in setting:
        ret['result'] = True
        ret['comment'] = 'Diagnostic setting {0} has been created.'.format(name)
        return ret

    ret['comment'] = 'Failed to create diagnostic setting {0}! ({1})'.format(name, setting.get('error'))
    if ret['result'] == False:
        ret['changes'] = {}
    return ret


async def absent(hub, ctx, name, resource_uri, connection_auth=None):
    '''
    .. versionadded:: 1.0.0

    Ensure a diagnostic setting does not exist for the specified resource uri.

    :param name: The name of the diagnostic setting.

    :param resource_uri: The identifier of the resource.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the 
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure diagnostic setting is absent:
            azurerm.monitor.diagnostic_setting.absent:
                - name: my_setting
                - resource_uri: my_resource
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

    setting = await hub.exec.azurerm.monitor.diagnostic_setting.get(
        name,
        resource_uri,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' in setting:
        ret['result'] = True
        ret['comment'] = 'Diagnostic setting {0} was not found.'.format(name)
        return ret

    elif ctx['test']:
        ret['comment'] = 'Diagnostic setting {0} would be deleted.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': setting,
            'new': {},
        }
        return ret

    deleted = await hub.exec.azurerm.monitor.diagnostic_setting.delete(
        name,
        resource_uri,
        **connection_auth
    )

    if deleted:
        ret['result'] = True
        ret['comment'] = 'Diagnostic setting {0} has been deleted.'.format(name)
        ret['changes'] = {
            'old': setting,
            'new': {}
        }
        return ret

    ret['comment'] = 'Failed to delete diagnostic setting {0}!'.format(name)
    return ret
