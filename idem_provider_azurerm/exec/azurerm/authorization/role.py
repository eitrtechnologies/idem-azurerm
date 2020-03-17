# -*- coding: utf-8 -*-
'''
Azure Resource Manager (ARM) Authorization Roles Execution Module

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

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.authorization.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError
    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def definitions_create_or_update(hub, defintion_id, scope, role_name=None, description=None, role_type=None,
                                       permissions=None, assignable_scopes=None, **kwargs):
    '''
    .. versionadded:: VERSION

    Creates or updates a role definition.

    :param definition_id: The ID of the role definiton.

    :param scope: The scope of the role definition.

    :param role_name: The role name.

    :param description: The role definition description.

    :param role_type: The role type.

    :param permissions: A list of dictionaries representing role definition Permission objects. Valid parameters are:
        - ``actions``: A list of strings representing allowed actions.
        - ``not_actions``: A list of strings representing denied actions.

    :param assignable_scopes: A list of role definition assignable scopes.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_create_or_update test_defintion_id test_scope

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        defmodel = await hub.exec.utils.azurerm.create_object_model(
            'authorization',
            'RoleDefinition',
            role_name=role_name,
            description=description,
            role_type=role_type,
            permissions=permissions,
            assignable_scopes=assignable_scopes,
            **kwargs
        )

    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        role = authconn.role_definitions.create(
            role_definition_id=definition_id,
            scope=scope,
            role_definition=defmodel
        )

        result = role.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def definitions_delete(hub, definition_id, scope, **kwargs):
    '''
    .. versionadded:: VERSION

    Deletes a role definition.

    :param definition_id: The ID of the role definition to delete.

    :param scope: The scope of the role definition.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_delete test_name test_scope

    '''
    result = False
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:

    role = authconn.role_definitions.delete(
        role_definition_id=definition_id,
        **kwargs
    )

    result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def definitions_get(hub, definition_id, scope, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Get role definition by name (GUID).

    :param definition_id: The ID of the role definition.

    :param scope: The scope of the role definition.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_get test_id test_scope

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        defs = authconn.role_definitions.get(
            scope=scope,
            role_definition_id=definition_id,
            **kwargs
        )

        result = defs.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def definitions_get_by_id(hub, definition_id, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets a role definition by ID.

    :param role_id: The fully qualified role definition ID. Use the format,
        /subscriptions/{guid}/providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId} for subscription
        level role definitions, or /providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId} for tenant
        level role definitions.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_get_by_id test_id

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        defs = authconn.role_definitions.get_by_id(
            role_definition_id=definition_id,
            **kwargs
        )

        result = defs.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def definitions_list(hub, scope, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Get all role definitions that are applicable at scope and above.

    :param scope: The scope of the role definition.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_list test_scope

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        defs = await hub.exec.utils.azurerm.paged_object_to_list(
            authconn.role_definitions.list(
                scope=scope,
                filter=kwargs.get('filter'),
                **kwargs
            )
        )

        result = defs
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_create(hub, name, scope, definition_id, principal_id, **kwargs):
    '''
    .. versionadded:: VERSION

    Creates a role assignment.

    :param name: The name of the role assignment to create. It can be any valid GUID.

    :param scope: The scope of the role assignment to create. The scope can be any REST resource instance.
        For example, use '/subscriptions/{subscription-id}/' for a subscription,
        '/subscriptions/{subscription-id}/resourceGroups/{resource-group-name}' for a resource group, and
        '/subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/providers/{resource-provider}/{resource-type}/{resource-name}'
        for a resource.

    :param definition_id: The role definition ID used in the role assignment.

    :param principal_id: The principal ID assigned to the role. This maps to the ID inside the Active Directory.
        It can point to a user, service principal, or security group.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_create test_name test_scope test_def test_principal

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        rolemodel = await hub.exec.utils.azurerm.create_object_model(
            'authorization',
            'RoleAssignmentProperties',
            role_definition_id=definition_id,
            principal_id=principal_id,
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        role = authconn.role_assignments.create(
            role_assignment_name=name,
            scope=scope,
            properties=rolemodel
        )

        result = role.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def assignments_create_by_id(hub, assignment_id, definition_id, principal_id, **kwargs):
    '''
    .. versionadded:: VERSION

    Creates a role assignment by ID.

    :param assignment_id: The fully qualified ID of the role assignment, including the scope, resource name and resource
        type. Use the format, /{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}.
        Example: /subscriptions/{subId}/resourcegroups/{rgname}//providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}.

    :param definition_id: The role definition ID used in the role assignment.

    :param principal_id: The principal ID assigned to the role. This maps to the ID inside the Active Directory.
        It can point to a user, service principal, or security group.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_create_by_id test_id test_def test_principal

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        rolemodel = await hub.exec.utils.azurerm.create_object_model(
            'authorization',
            'RoleAssignmentProperties',
            role_definition_id=definition_id,
            principal_id=principal_id,
            **kwargs
        )
    except TypeError as exc:
        result = {'error': 'The object model could not be built. ({0})'.format(str(exc))}
        return result

    try:
        role = authconn.role_assignments.create(
            role_assignment_id=assignment_id,
            properties=rolemodel
        )

        result = role.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}
    except SerializationError as exc:
        result = {'error': 'The object model could not be parsed. ({0})'.format(str(exc))}

    return result


async def assignments_delete(hub, name, scope, **kwargs):
    '''
    .. versionadded:: VERSION

    Deletes a role assignment.

    :param name: The name of the lock to be deleted.

    :param scope: The scope of the role assignment to delete.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_delete test_name test_scope

    '''
    result = False
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        role = authconn.role_assignments.delete(
            role_assignment_name=name,
            scope=scope,
            **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_delete_by_id(hub, assignment_id, **kwargs):
    '''
    .. versionadded:: VERSION

    Deletes a role assignment by ID.

    :param assignment_id: The fully qualified ID of the role assignment, including the scope, resource name and resource
        type. Use the format, /{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}.
        Example: /subscriptions/{subId}/resourcegroups/{rgname}//providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_delete_by_id test_id

    '''
    result = False
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        role = authconn.role_assignments.delete_by_id(
            role_assignment_id=assignment_id,
            **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_get(hub, name, scope, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Get the specified role assignment.

    :param name: The name of the role assignment to get.

    :param scope: The scope of the role assignment.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_get test_name test_scope

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        assigns = authconn.role_assignments.get(
            role_assignment_name=name,
            scope=scope,
            **kwargs
        )

        result = assigns.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_get_by_id(hub, assignment_id, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets a role assignment by ID.

    :param assignment_id: The fully qualified ID of the role assignment, including the scope, resource name and resource type.
        Use the format, /{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}. Example:
        /subscriptions/{subId}/resourcegroups/{rgname}//providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_get_by_id test_id

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        assigns = authconn.role_assignments.get_by_id(
            role_assignment_id=assignment_id,
            **kwargs
            )

        result = assigns.as_dict()
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_list(hub, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets all role assignments for the subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        assigns = await hub.exec.utils.azurerm.paged_object_to_list(
            authconn.role_assignments.list(
                filter=kwargs.get('filter'),
                **kwargs
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_list_for_resource(hub, name, resource_group, resource_provider_namespace, resource_type,
                                      parent_resource_path=None, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets all role assignments for a resource.

    :param name: The name of the resource to get role assignments for.

    :param resource_group: The name of the resource group.

    :param resource_provider_namespace: The namespace of the resource provider.

    :param resource_type: The resource type of the resource.

    :param parent_resource_path: The parent resource identity.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list_for_resource test_name test_group test_namespace \
                  test_type test_path

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    if parent_resource_path is None:
        parent_resource_path = ''

    try:
        assigns = await hub.exec.utils.azurerm.paged_object_to_list(
            authconn.role_assignments.list_for_resource(
                resource_name=name,
                resource_group_name=resource_group,
                resource_provider_namespace=resource_provider_namespace,
                resource_type=resource_type,
                parent_resource_path=parent_resource_path,
                filter=kwargs.get('filter'),
                **kwargs
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_list_for_resource_group(hub, name, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets all role assignments for a resource group.

    :param name: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list_for_resource_group test_group

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        assigns = await hub.exec.utils.azurerm.paged_object_to_list(
            authconn.role_assignments.list_for_resource_group(
                resource_group_name=name,
                filter=kwargs.get('filter'),
                **kwargs
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result


async def assignments_list_for_scope(hub, scope, **kwargs):
    '''
    .. versionadded:: 1.0.0

    Gets role assignments for a scope.

    :param scope: The scope of the role assignments.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list_for_scope test_scope

    '''
    result = {}
    authconn = await hub.exec.utils.azurerm.get_client('authorization', **kwargs)

    try:
        assigns = await hub.exec.utils.azurerm.paged_object_to_list(
            authconn.role_assignments.list_for_scope(
                scope=scope,
                filter=kwargs.get('filter'),
                **kwargs
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.utils.azurerm.log_cloud_error('authorization', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result
