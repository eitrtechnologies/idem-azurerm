# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Authorization Permissions Execution Module

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


async def permissions_list_for_resource(
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

    Gets all permissions the caller has for a resource.

    :param name: The name of the resource to get permissions for.

    :param resource_group: The name of the resource group containing the resource. The name is case insensitive.

    :param resource_provider_namespace: The namespace of the resource provider.

    :param resource_type: The resource type of the resource.

    :param parent_resource_path: (Optional) The namespace of the resource provider.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.permission.list_for_resource testname testgroup testnamespace testtype testpath

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    if parent_resource_path is None:
        parent_resource_path = ""

    try:
        perms = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.permissions.list_for_resource(
                resource_name=name,
                resource_group_name=resource_group,
                resource_provider_namespace=resource_provider_namespace,
                resource_type=resource_type,
                parent_resource_path=parent_resource_path,
                **kwargs,
            )
        )

        result = perms
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result


async def permissions_list_for_resource_group(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 1.0.0

    Gets all permissions the caller has for a resource group.

    :param name: The name of the resource group to get the permissions for. The name is case insensitive.

    CLI Example:

    .. code-block:: bash

        azurerm.authorization.permission.list_for_resource_group testname

    """
    result = {}
    authconn = await hub.exec.azurerm.utils.get_client(ctx, "authorization", **kwargs)

    try:
        perms = await hub.exec.azurerm.utils.paged_object_to_list(
            authconn.permissions.list_for_resource_group(
                resource_group_name=name, **kwargs
            )
        )

        result = perms
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "authorization", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
