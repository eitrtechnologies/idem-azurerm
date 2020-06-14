# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Management Lock State Module

.. versionadded:: 2.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed via acct. Note that the
    authentication parameters are case sensitive.

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
            default:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass

    The authentication parameters can also be passed as a dictionary of keyword arguments to the ``connection_auth``
    parameter of each state, but this is not preferred and could be deprecated in the future.

"""
# Import Python libs
from __future__ import absolute_import
import logging

log = logging.getLogger(__name__)


async def present_by_scope(
    hub,
    ctx,
    name,
    scope,
    lock_level,
    notes=None,
    owners=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a management lock exists by scope.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param scope: The scope for the lock. When providing a scope for the assignment,
        use '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups, and
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{resourceProviderNamespace}/{parentResourcePathIfPresent}/{resourceType}/{resourceName}'
        for resources.

    :param lock_level: The level of the lock. Possible values are: 'CanNotDelete' and 'ReadOnly'. CanNotDelete means
        authorized users are able to read and modify the resources, but not delete. ReadOnly means authorized users
        can only read from a resource, but they can't modify or delete it.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management lock exists by scope:
            azurerm.resource.management_lock.present_by_scope:
                - name: my_lock
                - scope: my_scope
                - lock_level: 'ReadOnly'
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    lock = await hub.exec.azurerm.resource.management_lock.get_by_scope(
        ctx, name, scope, azurerm_log_level="info", **connection_auth
    )

    if "error" not in lock:
        action = "update"
        if lock_level != lock.get("level"):
            ret["changes"]["level"] = {"old": lock.get("level"), "new": lock_level}

        if notes != lock.get("notes"):
            ret["changes"]["notes"] = {"old": lock.get("notes"), "new": notes}

        if owners:
            new_owners = owners.sort()
            lock_owners = lock.get("owners", [])
            if lock_owners:
                # Extracts the application_id value from each dictionary that represents a ManagementLockOwner object
                old_owners = [owner.get("application_id") for owner in lock_owners]
                old_owners = old_owners.sort()
            else:
                old_owners = []

            if old_owners != new_owners:
                ret["changes"]["owners"] = {"old": old_owners, "new": new_owners}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Management lock {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Management lock {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {"name": name, "scope": scope, "lock_level": lock_level,},
        }

        if owners:
            ret["changes"]["new"]["owners"] = owners
        if notes:
            ret["changes"]["new"]["notes"] = notes

    if ctx["test"]:
        ret["comment"] = "Management lock {0} would be created.".format(name)
        ret["result"] = None
        return ret

    lock_kwargs = kwargs.copy()
    lock_kwargs.update(connection_auth)

    lock = await hub.exec.azurerm.resource.management_lock.create_or_update_by_scope(
        ctx=ctx,
        name=name,
        scope=scope,
        lock_level=lock_level,
        notes=notes,
        owners=owners,
        **lock_kwargs,
    )

    if "error" not in lock:
        ret["result"] = True
        ret["comment"] = f"Management lock {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} management lock {1}! ({2})".format(
        action, name, lock.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent_by_scope(hub, ctx, name, scope, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a management lock does not exist by scope.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param scope: The scope for the lock. When providing a scope for the assignment,
        use '/subscriptions/{subscriptionId}' for subscriptions,
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}' for resource groups, and
        '/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/{resourceProviderNamespace}/{parentResourcePathIfPresent}/{resourceType}/{resourceName}' for resources.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management lock absent by scope:
            azurerm.resource.management_lock.absent_by_scope:
                - name: my_lock
                - scope: my_scope
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    lock = await hub.exec.azurerm.resource.management_lock.get_by_scope(
        ctx, name, scope, azurerm_log_level="info", **connection_auth
    )

    if "error" in lock:
        ret["result"] = True
        ret["comment"] = "Management lock {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Management lock {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": lock,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.resource.management_lock.delete_by_scope(
        ctx, name, scope, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Management lock {0} has been deleted.".format(name)
        ret["changes"] = {"old": lock, "new": {}}
        return ret

    ret["comment"] = "Failed to delete management lock {0}!".format(name)
    return ret


async def present_at_resource_level(
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
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a management lock exists at resource level.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain<, > %, &,
        :, ?, /, or any control characters.

    :param lock_level: The level of the lock. Possible values are: 'CanNotDelete' and 'ReadOnly'. CanNotDelete means
        authorized users are able to read and modify the resources, but not delete. ReadOnly means authorized users
        can only read from a resource, but they can't modify or delete it.

    :param resource_group: The name of the resource group containing the resource to lock.

    :param resource: The name of the resource to lock.

    :param resource_type: The resource type of the resource to lock.

    :param resource_provider_namespace: The resource provider namespace of the resource to lock.

    :param parent_resource_path: The parent resource identity.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management lock exists at resource level:
            azurerm.resource.management_lock.present_at_resource_level:
                - name: my_lock
                - resource_group: my_rg
                - resource: my_resource
                - resource_type: my_type
                - resource_provider_namespace: my_namespace
                - lock_level: 'ReadOnly'
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    lock = await hub.exec.azurerm.resource.management_lock.get_at_resource_level(
        ctx,
        name,
        resource_group,
        resource,
        resource_type,
        resource_provider_namespace,
        parent_resource_path,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in lock:
        action = "update"
        if lock_level != lock.get("level"):
            ret["changes"]["level"] = {"old": lock.get("level"), "new": lock_level}

        if notes != lock.get("notes"):
            ret["changes"]["notes"] = {"old": lock.get("notes"), "new": notes}

        if owners:
            new_owners = owners.sort()
            lock_owners = lock.get("owners", [])
            if lock_owners:
                # Extracts the application_id value from each dictionary that represents a ManagementLockOwner object
                old_owners = [owner.get("application_id") for owner in lock_owners]
                old_owners = old_owners.sort()
            else:
                old_owners = []

            if old_owners != new_owners:
                ret["changes"]["owners"] = {"old": old_owners, "new": new_owners}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Management lock {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Management lock {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "lock_level": lock_level,
                "resource": resource,
                "resource_type": resource_type,
                "resource_provider_namespace": resource_provider_namespace,
            },
        }

        if owners:
            ret["changes"]["new"]["owners"] = owners
        if notes:
            ret["changes"]["new"]["notes"] = notes
        if parent_resource_path:
            ret["changes"]["new"]["parent_resource_path"] = parent_resource_path

    if ctx["test"]:
        ret["comment"] = "Management lock {0} would be created.".format(name)
        ret["result"] = None
        return ret

    lock_kwargs = kwargs.copy()
    lock_kwargs.update(connection_auth)

    lock = await hub.exec.azurerm.resource.management_lock.create_or_update_at_resource_level(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        resource=resource,
        resource_type=resource_type,
        resource_provider_namespace=resource_provider_namespace,
        parent_resource_path=parent_resource_path,
        lock_level=lock_level,
        notes=notes,
        owners=owners,
        **lock_kwargs,
    )

    if "error" not in lock:
        ret["result"] = True
        ret["comment"] = f"Management lock {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} management lock {1}! ({2})".format(
        action, name, lock.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent_at_resource_level(
    hub,
    ctx,
    name,
    resource_group,
    resource,
    resource_type,
    resource_provider_namespace,
    parent_resource_path=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a management lock does not exist at the resource level.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param resource_group: The name of the resource group containing the resource with the lock to delete.

    :param resource: The name of the resource with the lock to delete.

    :param resource_type: The resource type of the resource with the lock to delete.

    :param resource_provider_namespace: The resource provider namespace of the resource with the lock to delete.

    :param parent_resource_path: The parent resource identity.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management lock absent at resource level:
            azurerm.resource.management_lock.absent_at_resource_level:
                - name: my_lock
                - resource_group: my_rg
                - resource: my_resource
                - resource_type: my_type
                - resource_provider_namespace: my_namespace
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    lock = await hub.exec.azurerm.resource.management_lock.get_at_resource_level(
        ctx,
        name,
        resource_group,
        resource,
        resource_type,
        resource_provider_namespace,
        parent_resource_path=parent_resource_path,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in lock:
        ret["result"] = True
        ret["comment"] = "Management lock {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Management lock {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": lock,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.resource.management_lock.delete_at_resource_level(
        ctx,
        name,
        resource_group,
        resource,
        resource_type,
        resource_provider_namespace,
        parent_resource_path=parent_resource_path,
        **connection_auth,
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Management lock {0} has been deleted.".format(name)
        ret["changes"] = {"old": lock, "new": {}}
        return ret

    ret["comment"] = "Failed to delete management lock {0}!".format(name)
    return ret


async def present(
    hub,
    ctx,
    name,
    lock_level,
    resource_group=None,
    notes=None,
    owners=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.0.0

    Ensure a management lock exists. By default this module ensures that the management lock exists at the
        subscription level. If you would like to ensure that the management lock exists at the resource group level
        instead, you can specify a resource group using the resource_group parameter.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param lock_level: The level of the lock. Possible values are: 'CanNotDelete' and 'ReadOnly'. CanNotDelete means
        authorized users are able to read and modify the resources, but not delete. ReadOnly means authorized users
        can only read from a resource, but they can't modify or delete it.

    :param resource_group: The name of the resource group. This is an optional parameter.

    :param notes: An optional string representing notes about the lock. Maximum of 512 characters.

    :param owners: An optional list of strings representing owners of the lock. Each string represents the application
        id of the lock owner.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management lock exists:
            azurerm.resource.management_lock.present:
                - name: my_lock
                - lock_level: 'ReadOnly'
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    if resource_group:
        lock = await hub.exec.azurerm.resource.management_lock.get_at_resource_group_level(
            ctx, name, resource_group, azurerm_log_level="info", **connection_auth
        )
    else:
        lock = await hub.exec.azurerm.resource.management_lock.get_at_subscription_level(
            ctx, name, azurerm_log_level="info", **connection_auth
        )

    if "error" not in lock:
        action = "update"
        if lock_level != lock.get("level"):
            ret["changes"]["level"] = {"old": lock.get("level"), "new": lock_level}

        if notes != lock.get("notes"):
            ret["changes"]["notes"] = {"old": lock.get("notes"), "new": notes}

        if owners:
            new_owners = owners.sort()
            lock_owners = lock.get("owners", [])
            if lock_owners:
                # Extracts the application_id value from each dictionary that represents a ManagementLockOwner object
                old_owners = [owner.get("application_id") for owner in lock_owners]
                old_owners = old_owners.sort()
            else:
                old_owners = []

            if old_owners != new_owners:
                ret["changes"]["owners"] = {"old": old_owners, "new": new_owners}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Management lock {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Management lock {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {"old": {}, "new": {"name": name, "lock_level": lock_level,}}

        if resource_group:
            ret["changes"]["new"]["resource_group"] = resource_group
        if owners:
            ret["changes"]["new"]["owners"] = owners
        if notes:
            ret["changes"]["new"]["notes"] = notes

    if ctx["test"]:
        ret["comment"] = "Management lock {0} would be created.".format(name)
        ret["result"] = None
        return ret

    lock_kwargs = kwargs.copy()
    lock_kwargs.update(connection_auth)

    if resource_group:
        lock = await hub.exec.azurerm.resource.management_lock.create_or_update_at_resource_group_level(
            ctx=ctx,
            name=name,
            resource_group=resource_group,
            lock_level=lock_level,
            notes=notes,
            owners=owners,
            **lock_kwargs,
        )
    else:
        lock = await hub.exec.azurerm.resource.management_lock.create_or_update_at_subscription_level(
            ctx=ctx,
            name=name,
            lock_level=lock_level,
            notes=notes,
            owners=owners,
            **lock_kwargs,
        )

    if "error" not in lock:
        ret["result"] = True
        ret["comment"] = f"Management lock {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} management lock {1}! ({2})".format(
        action, name, lock.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group=None, connection_auth=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Ensure a management lock does not exist. By default this module ensures that the management lock does not exist at
        the subscription level. If you would like to ensure that the management lock does not exist at the resource
        group level instead, you can specify a resource group using the resource_group parameter.

    :param name: The name of the lock. The lock name can be a maximum of 260 characters. It cannot contain <, > %, &,
        :, ?, /, or any control characters.

    :param resource_group: The name of the resource group. This is an optional parameter.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure management lock is absent:
            azurerm.resource.management_lock.absent:
                - name: my_lock
                - connection_auth: {{ profile }}

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    if resource_group:
        lock = await hub.exec.azurerm.resource.management_lock.get_at_resource_group_level(
            ctx, name, resource_group, azurerm_log_level="info", **connection_auth
        )
    else:
        lock = await hub.exec.azurerm.resource.management_lock.get_at_subscription_level(
            ctx, name, azurerm_log_level="info", **connection_auth
        )

    if "error" in lock:
        ret["result"] = True
        ret["comment"] = "Management lock {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Management lock {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": lock,
            "new": {},
        }
        return ret

    if resource_group:
        deleted = await hub.exec.azurerm.resource.management_lock.delete_at_resource_group_level(
            ctx, name, resource_group, **connection_auth
        )
    else:
        deleted = await hub.exec.azurerm.resource.management_lock.delete_at_subscription_level(
            ctx, name, **connection_auth
        )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Management lock {0} has been deleted.".format(name)
        ret["changes"] = {"old": lock, "new": {}}
        return ret

    ret["comment"] = "Failed to delete management lock {0}!".format(name)
    return ret
