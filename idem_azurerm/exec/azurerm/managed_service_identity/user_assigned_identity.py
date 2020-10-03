# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) MSI User Assigned Identity Execution Module

.. versionadded:: 4.0.0

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
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def create_or_update(
    hub, ctx, name, resource_group, tags=None, **kwargs,
):
    """
    .. versionadded:: 4.0.0

    Create or update an identity in the specified subscription and resource group.

    :param name: The name of the identity resource.

    :param resource_group: The resource group name assigned to the identity.

    :param tags: A dictionary of strings can be passed as tag metadata to the identity object.

    CLI Example:

    .. code-block:: bash

        azurerm.managed_service_identity.user_assigned_identity.create_or_update test_identity test_group

    """
    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(
            ctx, resource_group, **kwargs
        )

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return {
                "error": "Unable to determine location from resource group specified."
            }
        kwargs["location"] = rg_props["location"]

    result = {}
    msiconn = await hub.exec.azurerm.utils.get_client(ctx, "msi", **kwargs)

    try:
        identity = msiconn.user_assigned_identities.create_or_update(
            resource_group_name=resource_group, resource_name=name, tags=tags, **kwargs
        )
        result = identity.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def delete(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Delete an identity.

    :param name: The identity to delete.

    :param resource_group: The resource group name assigned to the identity.

    CLI Example:

    .. code-block:: bash

        azurerm.managed_service_identity.user_assigned_identity.delete test_identity test_group

    """
    result = False
    msiconn = await hub.exec.azurerm.utils.get_client(ctx, "msi", **kwargs)

    try:
        identity = msiconn.user_assigned_identities.delete(
            resource_group_name=resource_group, resource_name=name
        )
        result = True
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, resource_group, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets an identity.

    :param name: The identity to get.

    :param resource_group: The resource group name assigned to the identity.

    CLI Example:

    .. code-block:: bash

        azurerm.managed_service_identity.user_assigned_identity.get test_identity test_group

    """
    result = {}
    msiconn = await hub.exec.azurerm.utils.get_client(ctx, "msi", **kwargs)

    try:
        identity = msiconn.user_assigned_identities.get(
            resource_group_name=resource_group, resource_name=name
        )
        result = identity.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, resource_group=None, **kwargs):
    """
    .. versionadded:: 4.0.0

    Lists all the user assigned identities available under the specified subscription.

    CLI Example:

    .. code-block:: bash

        azurerm.managed_service_identity.user_assigned_identity.list

    """
    result = {}
    msiconn = await hub.exec.azurerm.utils.get_client(ctx, "msi", **kwargs)

    try:
        if resource_group:
            identities = await hub.exec.azurerm.utils.paged_object_to_list(
                msiconn.user_assigned_identities.list_by_resource_group(
                    resource_group_name=resource_group, **kwargs
                )
            )
        else:
            identities = await hub.exec.azurerm.utils.paged_object_to_list(
                msiconn.user_assigned_identities.list_by_subscription(**kwargs)
            )

        for identity in identities:
            result[identity["name"]] = identity
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
