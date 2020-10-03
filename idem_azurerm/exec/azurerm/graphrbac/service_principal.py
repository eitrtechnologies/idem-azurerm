# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Graph RBAC Service Principal Execution Module

.. versionadded:: 2.4.0

.. versionchanged:: 4.0.0

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
import logging

# Azure libs
HAS_LIBS = False
try:
    from azure.graphrbac.models.graph_error_py3 import GraphErrorException

    HAS_LIBS = True
except ImportError:
    pass


__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


async def get(hub, ctx, object_id, **kwargs):
    """
    .. versionadded:: 4.0.0

    Gets service principal information from the directory.

    :param object_id: The object ID of the service principal to get.

    CLI Example:

    .. code-block:: bash

        azurerm.graphrbac.service_principal.get test_id

    """
    result = {}
    graphconn = await hub.exec.azurerm.graphrbac.client.get(
        ctx, resource="https://graph.windows.net", **kwargs
    )

    try:
        principal = graphconn.service_principals.get(object_id=object_id)
        result = principal.as_dict()
    except GraphErrorException as exc:
        result = {"error": str(exc)}

    return result


async def list_(hub, ctx, sp_filter=None, **kwargs):
    """
    .. versionadded:: 2.4.0

    .. versionchanged:: 4.0.0

    Gets list of service principals from the current tenant.

    :param sp_filter: The filter to apply to the operation.

    CLI Example:

    .. code-block:: bash

        azurerm.graphrbc.service_principal.list sp_filter="displayName eq 'Test Buddy'"

    """
    result = {}
    graphconn = await hub.exec.azurerm.graphrbac.client.get(
        ctx, resource="https://graph.windows.net", **kwargs
    )

    try:
        principals = await hub.exec.azurerm.utils.paged_object_to_list(
            graphconn.service_principals.list(filter=sp_filter)
        )
        for principal in principals:
            result[principal["object_id"]] = principal
    except GraphErrorException as exc:
        result = {"error": str(exc)}

    return result
