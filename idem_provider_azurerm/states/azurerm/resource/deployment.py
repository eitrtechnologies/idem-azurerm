# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Deployment State Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 2.7.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 2.2.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 2.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 0.35.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.34.3
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.2
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

    Example configuration for Azure Resource Manager authentication:

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
# Import Python libs
from __future__ import absolute_import
import json
import logging

log = logging.getLogger(__name__)


async def present(hub, ctx, name, resource_group, deploy_mode='incremental', debug_settying='none', deploy_params=None,
                  parameters_link=None, deploy_template=None, template_link=None, tags=None, connection_auth=None,
                  **kwargs):
    '''
    .. versionadded:: 1.0.0

    Ensure a deployment exists.

    :param name: The name of the deployment to create or update.

    :param resource_group: The resource group name assigned to the deployment.

    :param deploy_mode: The mode that is used to deploy resources. This value can be either 'incremental' or 'complete'.
        In Incremental mode, resources are deployed without deleting existing resources that are not included in the
        template. In Complete mode, resources are deployed and existing resources in the resource group that are not
        included in the template are deleted. Be careful when using Complete mode as you may unintentionally delete
        resources.

    :param debug_setting: The debug setting of the deployment. The permitted values are 'none', 'requestContent',
        'responseContent', or 'requestContent,responseContent'. By logging information about the request or response,
        you could potentially expose sensitive data that is retrieved through the deployment operations.

    :param deploy_params: JSON string containing name and value pairs that define the deployment parameters for the
        template. You use this element when you want to provide the parameter values directly in the request rather
        than link to an existing parameter file. Use either the parameters_link property or the deploy_params property,
        but not both.

    :param parameters_link: The URI of a parameters file. You use this element to link to an existing parameters file.
        Use either the parameters_link property or the deploy_params property, but not both.

    :param deploy_template: JSON string of template content. You use this element when you want to pass the template
        syntax directly in the request rather than link to an existing template. Use either the template_link property
        or the deploy_template property, but not both.

    :param template_link: The URI of the template. Use either the template_link property or the deploy_template
        property, but not both.

    :param tags: A dictionary of strings can be passed as tag metadata to the resource group object.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure deployment exists:
            azurerm.resource.deployment.present:
                - name: my_lock
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

    deployment = await hub.exec.azurerm.resource.deployment.get(
        name,
        resource_group,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' not in deployment:
        tag_changes = await hub.exec.utils.dictdiffer.deep_diff(deployment.get('tags', {}), tags or {})
        if tag_changes:
            ret['changes']['tags'] = tag_changes

        # CHECK THIS TO SEE IF IT IS WORKING
        if deploy_mode != deployment.get('mode'):
            ret['changes']['deploy_mode'] = {
                'old': deployment.get('mode'),
                'new': deploy_mode
            }

        if debug_setting == deployment.get('debug_setting').get('detail_level'):
            ret['changes']['debug_setting']:
                'old': deployment.get('debug_setting'),
                'new': debug_setting
        '''
        if kwargs.get('notes', None) != lock.get('notes'):
            ret['changes']['notes'] = {
                'old': lock.get('notes'),
                'new': kwargs.get('notes')
            }
        '''

        if not ret['changes']:
            ret['result'] = True
            ret['comment'] = 'Deployment {0} is already present.'.format(name)
            return ret

        if ctx['test']:
            ret['result'] = None
            ret['comment'] = 'Deployment {0} would be updated.'.format(name)
            return ret

    else:
        ret['changes'] = {
            'old': {},
            'new': {
                'name': name,
                'resource_group': resource_group,
                'deploy_mode': deploy_mode,
                'debug_setting': debug_setting,
            }
        }

        if tags:
            ret['changes']['new']['tags'] = tags
        if deploy_params:
            ret['changes']['new']['deploy_params'] = deploy_params
        if parameters_link:
            ret['changes']['new']['parameters_link'] = parameters_link
        if deploy_template:
            ret['changes']['new']['deploy_template'] = deploy_template
        if template_link:
            ret['changes']['new']['template_link'] = template_link

    if ctx['test']:
        ret['comment'] = 'Deployment {0} would be created.'.format(name)
        ret['result'] = None
        return ret

    deployment_kwargs = kwargs.copy()
    deployment_kwargs.update(connection_auth)

    deployment = await hub.exec.azurerm.resource.deployment.create_or_update(
        name=name,
        resource_group=resource_group,
        deploy_mode=deploy_mode,
        debug_setting=debug_setting,
        deploy_params=deploy_params,
        parameters_link=parameters_link,
        deploy_template=deploy_template,
        template_link=template_link,
        tags=tags,
        **deployment_kwargs
    )

    if 'error' not in deployment:
        ret['result'] = True
        ret['comment'] = 'Deployment {0} has been created.'.format(name)
        return ret

    ret['comment'] = 'Failed to create deployment {0}! ({1})'.format(name, deployment.get('error'))
    if ret['result'] == False:
        ret['changes'] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None):
    '''
    .. versionadded:: 1.0.0

    Ensure a deployment does not exist.

    :param name: The name of the deployment to delete.

    :param resource_group: The name of the resource group assigned to the deployment.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure deployment is absent:
            azurerm.resource.deployment.absent:
                - name: my_lock
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

    deployment = await hub.exec.azurerm.resource.deployment.get(
        name,
        resource_group,
        azurearm_log_level='info',
        **connection_auth
    )

    if 'error' in deployment:
        ret['result'] = True
        ret['comment'] = 'Deployment {0} was not found.'.format(name)
        return ret

    elif ctx['test']:
        ret['comment'] = 'Deployment {0} would be deleted.'.format(name)
        ret['result'] = None
        ret['changes'] = {
            'old': deployment,
            'new': {},
        }
        return ret

    deleted = await hub.exec.azurerm.resource.deployment.delete(
        name,
        resource_group,
        **connection_auth
    )

    if deleted:
        ret['result'] = True
        ret['comment'] = 'Deployment {0} has been deleted.'.format(name)
        ret['changes'] = {
            'old': deployment,
            'new': {}
        }
        return ret

    ret['comment'] = 'Failed to delete deployment {0}!'.format(name)
    return ret
