# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Management Group Operations Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 4.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.23
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 4.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 4.6.2
    * `azure-mgmt-managementgroups <https://pypi.org/project/azure-mgmt-managementgroups/>`_ >= 0.2.0
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

# Azure libs
HAS_LIBS = False
try:
    #import azure.mgmt.managementgroups.models # pylint: disable=unused-import
    from azure.mgmt.managementgroups import ManagementGroupsAPI
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def _get_api_client(hub, **kwargs):
    '''
    .. versionadded:: VERSION
    
    Load the ManagementGroupsAPI client and returns the client object.
    
    '''
    credentials, subscription_id, cloud_env = await hub.exec.utils.azurerm.determine_auth(**kwargs)
    client = ManagementGroupsAPI(credentials)
    return client


async def create_or_update(hub, group_id, display_name=None, cache_control='no-cache', parent=None, **kwargs):
    '''
    .. versionadded:: VERSION

    Create or update a management group. If a management group is already created and a subsequent create request is
        issued with different properties, the management group properties will be updated.

    :param group_id: The ID of the Management Group to create or update. 

    :param display_name: The friendly name of the management group. If no value is passed then this field will be set
        to the groupId.

    :param cache_control: ADD DESCRIPTION HERE. Defaults to 'no-cache', which indicates that the request shouldn't
        utilize any caches.

    :param parent: The fully qualified ID for the parent management group. For example,
        /providers/Microsoft.Management/managementGroups/0000000-0000-0000-0000-000000000000.

    CLI Example:

    .. code-block:: bash

        azurerm.managementgroup.operations.create_or_update test_group test_name test_control test_parent

    '''
    result = {}
    manconn = await _get_api_client(**kwargs)

    if parent:
        parent = {'id': parent}

    try:
        group_details = await hub.exec.utils.azurerm.create_object_model(
            'managementgroups',
            'CreateManagementGroupDetails',
            parent=parent
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        group_request = await hub.exec.utils.azurerm.create_object_model(
            'managementgroups',
            'CreateManagementGroupRequest',
            display_name=display_name,
            details=group_details,
            **kwargs
        )

    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        group = manconn.management_groups.create_or_update(
            group_id=group_id,
            create_management_group_request=group_request,
            cache_control=cache_control,
        )

        result = group.result()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('managementgroup', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result
