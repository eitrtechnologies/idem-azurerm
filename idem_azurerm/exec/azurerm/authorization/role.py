# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Authorization Roles Execution Module

.. versionadded:: 1.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function or via acct in order to work properly.

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

"""

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


async def definitions_get(hub, ctx, role_id, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get role definition by name (GUID).

    :param role_id: The ID of the role definition.

    :param scope: The scope of the role definition.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_get testid testscope

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        defs = authconn.role_definitions.get(
            scope=scope, role_definition_id=role_id, **kwargs
        )

        result = defs.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def definitions_get_by_id(hub, ctx, role_id, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a role definition by ID.

    :param role_id: The fully qualified role definition ID. Use the format,
        /subscriptions/{guid}/providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId} for subscription
        level role definitions, or /providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId} for tenant
        level role definitions.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_get_by_id testid

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        defs = authconn.role_definitions.get_by_id(role_definition_id=role_id, **kwargs)

        result = defs.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def definitions_list(hub, ctx, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get all role definitions that are applicable at scope and above.

    :param scope: The scope of the role definition.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.definitions_list testscope

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        defs = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.role_definitions.list(
                scope=scope, filter=kwargs.get("filter"), **kwargs
            )
        )

        result = defs
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def assignments_get(hub, ctx, name, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get the specified role assignment.

    :param name: The name of the role assignment to get.

    :param scope: The scope of the role assignment.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_get testname testscope

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        assigns = authconn.role_assignments.get(
            role_assignment_name=name, scope=scope, **kwargs
        )

        result = assigns.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def assignments_get_by_id(hub, ctx, assignment_id, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a role assignment by ID.

    :param assignment_id: The fully qualified ID of the role assignment, including the scope, resource name and resource type.
        Use the format, /{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}. Example:
        /subscriptions/{subId}/resourcegroups/{rgname}//providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_get_by_id testid

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        assigns = authconn.role_assignments.get_by_id(
            role_assignment_id=assignment_id, **kwargs
        )

        result = assigns.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def assignments_list(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets all role assignments for the subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        assigns = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.role_assignments.list(filter=kwargs.get("filter"), **kwargs)
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def assignments_list_for_resource(
    hub,
    ctx,
    name,
    resource_group,
    resource_provider_namespace,
    resource_type,
    parent_resource_path=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Gets all role assignments for a resource.

    :param name: The name of the resource to get role assignments for.

    :param resource_group: The name of the resource group.

    :param resource_provider_namespace: The namespace of the resource provider.

    :param resource_type: The resource type of the resource.

    :param parent_resource_path: The parent resource identity.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list_for_resource testname testgroup testnamespace \
                  testtype testpath

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    if parent_resource_path is None:
        parent_resource_path = ""

    try:
        assigns = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.role_assignments.list_for_resource(
                resource_name=name,
                resource_group_name=resource_group,
                resource_provider_namespace=resource_provider_namespace,
                resource_type=resource_type,
                parent_resource_path=parent_resource_path,
                filter=kwargs.get("filter"),
                **kwargs,
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def assignments_list_for_resource_group(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets all role assignments for a resource group.

    :param name: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list_for_resource_group testgroup

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        assigns = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.role_assignments.list_for_resource_group(
                resource_group_name=name, filter=kwargs.get("filter"), **kwargs
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def assignments_list_for_scope(hub, ctx, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets role assignments for a scope.

    :param scope: The scope of the role assignments.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.role.assignments_list_for_scope testscope

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        assigns = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.role_assignments.list_for_scope(
                scope=scope, filter=kwargs.get("filter"), **kwargs
            )
        )

        result = assigns
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
