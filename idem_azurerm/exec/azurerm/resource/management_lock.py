# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Management Lock Execution Module

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
    import azure.mgmt.resource.resources.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

log = logging.getLogger(__name__)


async def create_or_update_at_resource_group_level(
    hub, ctx, name, resource_group, lock_level, notes=None, owners=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Creates or updates a management lock at the resource group level. When you apply a lock at a parent scope,
        all child resources inherit the same lock. To create management locks, you must have access to
        Microsoft.Authorization/* or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param resource_group: The name of the resource group.

    :param lock_level: The level of the lock. Possible values are: 'NotSpecified', 'CanNotDelete', & 'ReadOnly'.
        CanNotDelete means authorized users are able to read and modify the resources, but not delete. ReadOnly means
        authorized users can only read from a resource, but they can't modify or delete it.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.create_or_update_at_resource_group_level test_name test_group test_level

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    # Converts each application id in the owners list into a dictionary that represents a ManagementLockOwner object
    if owners:
        lock_owners = [{"application_id": owner} for owner in owners]
    else:
        lock_owners = []

    try:
        lockmodel = await hub.exec.azurerm.utils.create_object_model(
            "resource.locks",
            "ManagementLockObject",
            level=lock_level,
            notes=notes,
            owners=lock_owners,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        lock = lckconn.management_locks.create_or_update_at_resource_group_level(
            resource_group_name=resource_group, lock_name=name, parameters=lockmodel
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete_at_resource_group_level(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes a management lock at the resource group level. To delete management locks, you must have access to
        Microsoft.Authorization/* or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock to be deleted.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.delete_at_resource_group_level test_name test_group

    """
    result = False
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        lock = lckconn.management_locks.delete_at_resource_group_level(
            resource_group_name=resource_group, lock_name=name, **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_at_resource_group_level(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a management lock at the resource group level.

    :param name: The name of the lock to get.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.get_at_resource_group_level test_name test_group

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        lock = lckconn.management_locks.get_at_resource_group_level(
            resource_group_name=resource_group, lock_name=name, **kwargs
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update_by_scope(
    hub, ctx, name, scope, lock_level, notes=None, owners=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Create or update a management lock by scope. When you apply a lock at a parent scope, all child resources inherit
        the same lock. To create management locks, you must have access to Microsoft.Authorization/* or
        Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param scope: The scope for the lock. When providing a scope for the assignment,
        use '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups, and
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{resourceProviderNamespace}/{parentResourcePathIfPresent}/{resourceType}/{resourceName}'
        for resources.

    :param lock_level: The level of the lock. Possible values are: 'NotSpecified', 'CanNotDelete', & 'ReadOnly'.
        CanNotDelete means authorized users are able to read and modify the resources, but not delete. ReadOnly means
        authorized users can only read from a resource, but they can't modify or delete it.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.create_or_update_by_scope test_name test_scope test_level

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    # Converts each application id in the owners list into a dictionary that represents a ManagementLockOwner object
    if owners:
        lock_owners = [{"application_id": owner} for owner in owners]
    else:
        lock_owners = []

    try:
        lockmodel = await hub.exec.azurerm.utils.create_object_model(
            "resource.locks",
            "ManagementLockObject",
            level=lock_level,
            notes=notes,
            owners=lock_owners,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        lock = lckconn.management_locks.create_or_update_by_scope(
            scope=scope, lock_name=name, parameters=lockmodel
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete_by_scope(hub, ctx, name, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Delete a management lock by scope. To delete management locks, you must have access to Microsoft.Authorization/*
        or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock to be deleted.

    :param scope: The scope for the lock. When providing a scope for the assignment,
        use '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups, and
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{resourceProviderNamespace}/{parentResourcePathIfPresent}/{resourceType}/{resourceName}'
        for resources.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.delete_by_scope test_name test_scope

    """
    result = False
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        lock = lckconn.management_locks.delete_by_scope(
            scope=scope, lock_name=name, **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_by_scope(hub, ctx, name, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Get a management lock by scope.

    :param name: The name of the lock to get.

    :param scope: The scope for the lock. When providing a scope for the assignment,
        use '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups, and
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{resourceProviderNamespace}/{parentResourcePathIfPresent}/{resourceType}/{resourceName}'
        for resources.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.get_by_scope test_name test_scope

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        lock = lckconn.management_locks.get_by_scope(
            scope=scope, lock_name=name, **kwargs
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update_at_resource_level(
    hub,
    ctx,
    name,
    lock_level,
    resource_group,
    resource,
    resource_type,
    resource_provider_namespace,
    parent_resource_path=None,
    notes=None,
    owners=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Creates or updates a management lock at the resource level or any level below the resource. When you apply a lock
        at a parent scope, all child resources inherit the same lock. To create management locks, you must have access
        to Microsoft.Authorization/* or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param lock_level: The level of the lock. Possible values are: 'NotSpecified', 'CanNotDelete', & 'ReadOnly'.
        CanNotDelete means authorized users are able to read and modify the resources, but not delete. ReadOnly means
        authorized users can only read from a resource, but they can't modify or delete it.

    :param resource_group: The name of the resource group containing the resource to lock.

    :param resource: The name of the resource to lock.

    :param resource_type: The resource type of the resource to lock.

    :param resource_provider_namespace: The resource provider namespace of the resource to lock.

    :param parent_resource_path: The parent resource identity.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.create_or_update_at_resource_level test_name test_level test_group \
                  test_resource test_type test_namespace

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    # Converts each application id in the owners list into a dictionary that represents a ManagementLockOwner object
    if owners:
        lock_owners = [{"application_id": owner} for owner in owners]
    else:
        lock_owners = []

    try:
        lockmodel = await hub.exec.azurerm.utils.create_object_model(
            "resource.locks",
            "ManagementLockObject",
            level=lock_level,
            notes=notes,
            owners=lock_owners,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    if parent_resource_path is None:
        parent_resource_path = ""

    try:
        lock = lckconn.management_locks.create_or_update_at_resource_level(
            resource_group_name=resource_group,
            lock_name=name,
            resource_name=resource,
            resource_provider_namespace=resource_provider_namespace,
            resource_type=resource_type,
            parent_resource_path=parent_resource_path,
            parameters=lockmodel,
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete_at_resource_level(
    hub,
    ctx,
    name,
    resource_group,
    resource,
    resource_type,
    resource_provider_namespace,
    parent_resource_path=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Deletes the management lock of a resource or any level below the resource. When you apply a lock
        at a parent scope, all child resources inherit the same lock. To delete management locks, you must have access
        to Microsoft.Authorization/* or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock to delete.

    :param resource_group: The name of the resource group containing the resource with the lock to delete.

    :param resource: The name of the resource with the lock to delete.

    :param resource_type: The resource type of the resource with the lock to delete.

    :param resource_provider_namespace: The resource provider namespace of the resource with the lock to delete.

    :param parent_resource_path: The parent resource identity.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.delete_at_resource_level test_name test_group test_resource \
                  test_type test_namespace

    """
    result = False
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    if parent_resource_path is None:
        parent_resource_path = ""

    try:
        lock = lckconn.management_locks.delete_at_resource_level(
            lock_name=name,
            resource_group_name=resource_group,
            resource_name=resource,
            resource_provider_namespace=resource_provider_namespace,
            resource_type=resource_type,
            parent_resource_path=parent_resource_path,
            **kwargs,
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_at_resource_level(
    hub,
    ctx,
    name,
    resource_group,
    resource,
    resource_type,
    resource_provider_namespace,
    parent_resource_path=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Get the management lock of a resource or any level below resource.

    :param name: The name of the lock.

    :param resource_group: The name of the resource group.

    :param resource: The name of the resource.

    :param resource_type: The type of the resource.

    :param resource_provider_namespace: The namespace of the resource provider.

    :param parent_resource_path: The parent resource identity.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.get_at_resource_level test_name test_group test_resource \
                  test_type test_namespace

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    if parent_resource_path is None:
        parent_resource_path = ""

    try:
        lock = lckconn.management_locks.get_at_resource_level(
            lock_name=name,
            resource_group_name=resource_group,
            resource_name=resource,
            resource_provider_namespace=resource_provider_namespace,
            resource_type=resource_type,
            parent_resource_path=parent_resource_path,
            **kwargs,
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def create_or_update_at_subscription_level(
    hub, ctx, name, lock_level, notes=None, owners=None, **kwargs
):
    """
    .. versionadded:: 1.0.0

    Creates or updates a management lock at the subscription level. When you apply a lock at a parent scope,
        all child resources inherit the same lock. To create management locks, you must have access to
        Microsoft.Authorization/* or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param lock_level: The level of the lock. Possible values are: 'NotSpecified', 'CanNotDelete', & 'ReadOnly'.
        CanNotDelete means authorized users are able to read and modify the resources, but not delete. ReadOnly means
        authorized users can only read from a resource, but they can't modify or delete it.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.create_or_update_at_subscription_level test_name test_level

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    # Converts each application id in the owners list into a dictionary that represents a ManagementLockOwner object
    if owners:
        lock_owners = [{"application_id": owner} for owner in owners]
    else:
        lock_owners = []

    try:
        lockmodel = await hub.exec.azurerm.utils.create_object_model(
            "resource.locks",
            "ManagementLockObject",
            level=lock_level,
            notes=notes,
            owners=lock_owners,
            **kwargs,
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        lock = lckconn.management_locks.create_or_update_at_subscription_level(
            lock_name=name, parameters=lockmodel
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete_at_subscription_level(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Deletes the management lock at the subscription level. To delete management locks, you must have access to
        Microsoft.Authorization/* or Microsoft.Authorization/locks/* actions.

    :param name: The name of the lock to be deleted.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.delete_at_subscription_level test_name

    """
    result = False
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        lock = lckconn.management_locks.delete_at_subscription_level(
            lock_name=name, **kwargs
        )

        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get_at_subscription_level(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets a management lock at the subscription level.

    :param name: The name of the lock to get.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.get_at_subscription_level test_name

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        lock = lckconn.management_locks.get_at_subscription_level(
            lock_name=name, **kwargs
        )

        result = lock.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_at_resource_group_level(hub, ctx, resource_group, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets all the management locks for a resource group.

    :param resource_group: The name of the resource group containing the locks to get.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.list_at_resource_group_level test_group

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        result = await hub.exec.azurerm.utils.paged_object_to_list(
            lckconn.management_locks.list_at_resource_group_level(
                resource_group_name=resource_group, filter=kwargs.get("filter")
            )
        )

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_at_resource_level(
    hub,
    ctx,
    resource_group,
    resource,
    resource_type,
    resource_provider_namespace,
    parent_resource_path=None,
    **kwargs,
):
    """
    .. versionadded:: 1.0.0

    Get the management lock of a resource or any level below resource.

    :param resource_group: The name of the resource group.

    :param resource: The name of the resource.

    :param resource_type: The type of the resource.

    :param resource_provider_namespace: The namespace of the resource provider.

    :param parent_resource_path: The parent resource identity.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.list_at_resource_level test_group test_resource test_type \
                  test_namespace test_path

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    if parent_resource_path is None:
        parent_resource_path = ""

    try:
        result = await hub.exec.azurerm.utils.paged_object_to_list(
            lckconn.management_locks.list_at_resource_level(
                resource_group_name=resource_group,
                resource_name=resource,
                resource_provider_namespace=resource_provider_namespace,
                resource_type=resource_type,
                parent_resource_path=parent_resource_path,
                filter=kwargs.get("filter"),
            )
        )

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_at_subscription_level(hub, ctx, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets all the management locks for a subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.list_at_subscription_level

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        result = await hub.exec.azurerm.utils.paged_object_to_list(
            lckconn.management_locks.list_at_subscription_level(
                filter=kwargs.get("filter")
            )
        )

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_by_scope(hub, ctx, scope, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets all the management locks for a scope.

    :param scope: The scope for the lock. When providing a scope for the assignment,
        use '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups, and
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{resourceProviderNamespace}/{parentResourcePathIfPresent}/{resourceType}/{resourceName}'
        for resources.

    CLI Example:

    .. code-block:: bash

        azurerm.resource.management_lock.list_by_scope test_scope

    """
    result = {}
    lckconn = await hub.exec.azurerm.utils.get_client(ctx, "managementlock", **kwargs)

    try:
        result = await hub.exec.azurerm.utils.paged_object_to_list(
            lckconn.management_locks.list_by_scope(
                scope=scope, filter=kwargs.get("filter")
            )
        )

    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
