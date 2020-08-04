# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Management Group Operations Execution Module

.. versionadded:: 2.0.0

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
    import azure.mgmt.managementgroups.models  # pylint: disable=unused-import
    from azure.mgmt.managementgroups import ManagementGroupsAPI
    from azure.mgmt.managementgroups.models.error_response_py3 import (
        ErrorResponseException,
    )
    from msrest.exceptions import SerializationError
    from msrestazure.azure_exceptions import CloudError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


async def get_api_client(hub, ctx, **kwargs):
    """
    .. versionadded:: 2.0.0

    Load the ManagementGroupsAPI client and returns the client object.

    """
    (
        credentials,
        subscription_id,
        cloud_env,
    ) = await hub.exec.azurerm.utils.determine_auth(ctx, **kwargs)
    client = ManagementGroupsAPI(credentials=credentials, base_url=None)
    return client


async def create_or_update(hub, ctx, name, display_name=None, parent=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Create or update a management group. If a management group is already created and a subsequent create request is
        issued with different properties, the management group properties will be updated.

    :param name: The ID of the management group. For example, 00000000-0000-0000-0000-000000000000.

    :param display_name: The friendly name of the management group. If no value is passed then this field will be set
        to the name of the management group.

    :param parent: The fully qualified ID for the parent management group. For example,
        /providers/Microsoft.Management/managementGroups/0000000-0000-0000-0000-000000000000.

    CLI Example:

    .. code-block:: bash

        azurerm.managementgroup.operations.create_or_update test_name test_display test_parent

    """
    result = {}
    manconn = await hub.exec.azurerm.managementgroup.operations.get_api_client(
        ctx, **kwargs
    )

    if parent:
        parent = {"id": parent}

    try:
        group_details = await hub.exec.azurerm.utils.create_object_model(
            "managementgroups", "CreateManagementGroupDetails", parent=parent
        )
    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        group_request = await hub.exec.azurerm.utils.create_object_model(
            "managementgroups",
            "CreateManagementGroupRequest",
            display_name=display_name,
            details=group_details,
            **kwargs,
        )

    except TypeError as exc:
        result = {
            "error": "The object model could not be built. ({0})".format(str(exc))
        }
        return result

    try:
        mgroup = manconn.management_groups.create_or_update(
            group_id=name, create_management_group_request=group_request,
        )

        mgroup.wait()
        result = mgroup.result()
    except ErrorResponseException as exc:
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {
            "error": "The object model could not be parsed. ({0})".format(str(exc))
        }

    return result


async def delete(hub, ctx, name, **kwargs):
    """
    .. versionadded:: 2.0.0

    Delete management group. If a management group contains child resources, the request will fail.

    :param name: The ID of the management group.

    CLI Example:

    .. code-block:: bash

        azurerm.managementgroup.operations.delete test_name test

    """
    result = False
    manconn = await hub.exec.azurerm.managementgroup.operations.get_api_client(
        ctx, **kwargs
    )

    try:
        mgroup = manconn.management_groups.delete(group_id=name,)

        result = True
    except ErrorResponseException as exc:
        result = {"error": str(exc)}

    return result


async def get(hub, ctx, name, expand=None, recurse=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    Get the details of the specified management group.

    :param name: The ID of the management group.

    :param expand: The expand parameter allows clients to request inclusion of children in the response payload.
        Possible values include: 'children'. Defaults to None.

    :param recurse: The recurse boolean parameter allows clients to request inclusion of entire hierarchy in the
        response payload. Note that expand must be set to 'children' if recurse is set to True.

    CLI Example:

    .. code-block:: bash

        azurerm.managementgroup.operations.get test_name test_expand test_recurse

    """
    result = {}
    manconn = await hub.exec.azurerm.managementgroup.operations.get_api_client(
        ctx, **kwargs
    )

    try:
        mgroup = manconn.management_groups.get(
            group_id=name, expand=expand, recurse=recurse,
        )

        result = mgroup.as_dict()
    except ErrorResponseException as exc:
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, skip_token=None, **kwargs):
    """
    .. versionadded:: 2.0.0

    List management groups for the authenticated user.

    :param skip_token: Page continuation token is only used if a previous operation returned a partial result.
        If a previous response contains a nextLink element, the value of the nextLink element will include a token
        parameter that specifies a starting point to use for subsequent calls. Defaults to None.

    CLI Example:

    .. code-block:: bash

        azurerm.managementgroup.operations.list test_token

    """
    result = {}
    manconn = await hub.exec.azurerm.managementgroup.operations.get_api_client(
        ctx, **kwargs
    )

    try:
        mgroups = await hub.exec.azurerm.utils.paged_object_to_list(
            manconn.management_groups.list(skip_token=skip_token,)
        )

        for mgroup in mgroups:
            result[mgroup["display_name"]] = mgroup
    except ErrorResponseException as exc:
        result = {"error": str(exc)}

    return result
